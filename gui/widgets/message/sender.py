from asyncio.streams import StreamWriter
from ssl import SSLSocket
from uuid import UUID

from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher

from ..utils.encryption import pack_data, encrypt_aes
from . import ChunkSize, MsgType, Tags, generate_header, msg_encrypt



class Sender():
    def __init__(
            self, socket: SSLSocket, name: str, cipher: PKCS1OAEP_Cipher,
            server_pubkey: bytes, chunk_size: ChunkSize = ChunkSize.K64
    ) -> None:

        self.s = socket
        self.chunk_size = chunk_size.value
        self._name = name.encode()
        self._cipher = cipher
        self.server = server_pubkey

    def send_message(
            self, msg: bytes, typ: MsgType, pubkey: bytes,
            chatroom_id: UUID, basename: str = ""
    ) -> None:

        self._send_block(typ.value)
        self._send_block(len(msg).to_bytes(4, "big"))

        self._send_block(b'1' if basename else b'0')
        self._send_block(msg_encrypt(basename.encode(), self.server))

        self._send_block(msg_encrypt(chatroom_id.bytes, self.server))

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
            self, socket: StreamWriter, cipher: PKCS1OAEP_Cipher,
            chunk_size: ChunkSize = ChunkSize.K64
    ) -> None:

        self.s = socket
        self.chunk_size = chunk_size.value
        self._cipher = cipher

    async def send_message(
            self, msg: bytes, tags: Tags, pubkey: bytes
    ) -> None:

        tag_list = generate_header(tags, pubkey)

        for header_tag in tag_list:
            await self._send_block(header_tag)

        # Separator that differentiates header tags from actual data
        await self._send_block(b'<!DATA>')

        sz = self.chunk_size
        for i in range(0, len(msg), sz):
            chunk = msg[i:i + sz]
            await self._send_block(chunk)

        # END tag to tell receiver to stop reading stream
        await self._send_block(b'MSGEND')

    async def _send_block(self, data: bytes):
        self.s.write(len(data).to_bytes(4, "big"))
        await self.s.drain()
        self.s.write(data)
        await self.s.drain()
