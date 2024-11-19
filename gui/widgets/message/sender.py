from asyncio.streams import StreamWriter
import os
from ssl import SSLSocket
from uuid import UUID

from ..utils.encryption import pack_data, encrypt_aes
from . import (
    ChunkSize,
    MsgType,
    Tags,
    generate_header,
    msg_encrypt,
    FILELIKE,
    PICTURE_EXT,
)


class Sender():
    def __init__(
            self, socket: SSLSocket, name: str, server_pubkey: bytes,
            chunk_size: ChunkSize = ChunkSize.K64
    ) -> None:

        self.s = socket
        self.chunk_size = chunk_size.value
        self._name = name.encode()
        self.server = server_pubkey

    def send_message(
            self, msg: bytes, typ: MsgType, pubkey: bytes,
            chatroom_id: UUID, basename: str = ""
    ) -> None:

        self._send_block(typ.value)
        self._send_block(len(msg).to_bytes(4, "big"))
        self._send_block(msg_encrypt(chatroom_id.bytes, self.server))

        if typ in FILELIKE:
            print(basename)
            self._send_block(msg_encrypt(basename.encode(), self.server))

            _, ext = os.path.splitext(basename)
            if typ == MsgType.VIDEO or ext in PICTURE_EXT:
                # This one should tell a server whether message
                # should have preview or not 
                # Client should send both preveiw and not compressed content
                # Thus preview byte is always "1"(True) on client side
                # as client is responsible for sending it
                self._send_block(b'1')

        # Separator that differentiates header tags from actual data
        self._send_block(b'<!DATA>')

        data = pack_data(encrypt_aes(self._name + b'<SEP>' + msg), pubkey)
        sz = self.chunk_size
        for i in range(0, len(data), sz):
            chunk = data[i:i + sz]
            self._send_block(chunk)

        # END tag to tell receiver to stop reading stream
        self._send_block(b'MSGEND')

    def _send_block(self, data: bytes):
        self.s.send(len(data).to_bytes(4, "big"))
        self.s.send(data)

class AsyncSender():
    def __init__(
            self, chunk_size: ChunkSize = ChunkSize.K64
    ) -> None:

        self.chunk_size = chunk_size.value

    async def send_message(
        self, tags: Tags, msg: bytes, sock: StreamWriter, pubkey: bytes
    ) -> None:

        tag_list = generate_header(tags, pubkey)

        for header_tag in tag_list:
            await self._send_block(header_tag, sock)

        # Separator that differentiates header tags from actual data
        await self._send_block(b'<!DATA>', sock)

        data = pack_data(encrypt_aes(msg), pubkey)
        sz = self.chunk_size
        for i in range(0, len(data), sz):
            chunk = data[i:i + sz]
            await self._send_block(chunk, sock)

        # END tag to tell receiver to stop reading stream
        await self._send_block(b'MSGEND', sock)

    async def _send_block(self, data: bytes, sock: StreamWriter):
        sock.write(len(data).to_bytes(4, "big"))
        await sock.drain()
        sock.write(data)
        await sock.drain()

