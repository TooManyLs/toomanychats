from ssl import SSLSocket

from ..utils.encryption import pack_data, encrypt_aes
from . import ChunkSize, MsgType


class Sender():
    def __init__(self, socket: SSLSocket,
                 chunk_size: ChunkSize = ChunkSize.K64) -> None:

        self.s = socket
        self.chunk_size = chunk_size.value


    def send_message(self, msg: bytes, typ: MsgType, pubkey: bytes,
                     basename: str = "") -> None:

        # Prevent possible names from tripping receiver
        if basename == "MSGEND" or basename == "<!DATA>":
            basename += "_"

        self._send_block(typ.value)
        self._send_block(len(msg).to_bytes(4, "big"))

        if basename:
            self._send_block(b'1')

            self._send_block(basename.encode())
        else:
            self._send_block(b'0')

        # Separator that differentiates header tags from actual data
        self._send_block(b'<!DATA>')

        data = pack_data(encrypt_aes(msg), pubkey)
        sz = self.chunk_size
        for i in range(0, len(data), sz):
            chunk = data[i:i + sz]
            self._send_block(chunk)

        # END tag to tell receiver to stop reading stream
        self._send_block(b'MSGEND')

    def _send_block(self, data: bytes):
        self.s.send(len(data).to_bytes(4, "big"))
        self.s.send(data)

