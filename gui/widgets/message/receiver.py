from ssl import SSLSocket

from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher

from ..utils.encryption import unpack_data, decrypt_aes
from . import ChunkSize


class Receiver():
    def __init__(self, socket: SSLSocket, cipher: PKCS1OAEP_Cipher,
                 chunk_size: ChunkSize = ChunkSize.K64) -> None:

        self.s = socket
        self.cipher = cipher
        self.chunk_size = chunk_size.value


    def receive_message(self) -> tuple[bytes, bytes]:
        is_header = True
        chunks = []
        header = b''

        while True:
            length_bytes = self.s.recv(4)
            length = int.from_bytes(length_bytes, "big")
            chunk = self.s.recv(length)

            if chunk:
                if chunk == b'MSGEND':
                    break

                # Separate header tags from message content
                if chunk == b'<!DATA>':
                    header = b''.join(chunks)
                    chunks.clear()
                    continue

                if is_header:
                    chunks.append(length_bytes)
                chunks.append(chunk)
            else:
                raise RuntimeError("Socket connection broken")

        encrypted = b''.join(chunks)
        data = self.decrypt_message(encrypted)
        return header, data

    def decrypt_message(self, data: bytes) -> bytes:
        enc_data, enc_aes, _ = unpack_data(data)
        aes = self.cipher.decrypt(enc_aes)
        msg = decrypt_aes(enc_data, aes)

        return msg

