from asyncio.streams import StreamReader
from ssl import SSLSocket
from datetime import UTC, datetime

from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher


from ..utils.encryption import unpack_data, decrypt_aes
from . import ChunkSize, HeaderParser, Tags


def decrypt_message(cipher: PKCS1OAEP_Cipher, data: bytes) -> bytes:
    enc_data, enc_aes, _ = unpack_data(data)
    aes = cipher.decrypt(enc_aes)
    msg = decrypt_aes(enc_data, aes)

    return msg

class Receiver():
    def __init__(self, socket: SSLSocket, cipher: PKCS1OAEP_Cipher,
                 chunk_size: ChunkSize = ChunkSize.K64) -> None:

        self.s = socket
        self.cipher = cipher
        self.chunk_size = chunk_size.value

    def receive_message(self) -> tuple[Tags, bytes]:
        is_header = True
        chunks = []
        header = b''

        while True:
            length_bytes = self.s.recv(4)
            length = int.from_bytes(length_bytes, "big")

            # For some reason client buffer limit is 16KB and I can't
            # change it, so I have to rely on this workaround that
            # slows down the receiving 😢
            bytes_read = 0
            chunk = b''
            while bytes_read < length:
                dat = self.s.recv(length - bytes_read)
                chunk += dat
                bytes_read += len(dat)

            if chunk:
                if chunk == b'MSGEND':
                    break

                # Separate header tags from message content
                if chunk == b'<!DATA>':
                    header = b''.join(chunks)
                    chunks.clear()
                    is_header = False
                    continue

                if is_header:
                    chunks.append(length_bytes)
                chunks.append(chunk)
            else:
                raise RuntimeError("Socket connection broken")

        tags = HeaderParser(header, self.cipher).tags

        encrypted = b''.join(chunks)
        data = decrypt_message(self.cipher, encrypted)
        return tags, data

class AsyncReceiver():
    def __init__(self, socket: StreamReader, cipher: PKCS1OAEP_Cipher,
                 chunk_size: ChunkSize = ChunkSize.K64) -> None:

        self.s = socket
        self.cipher = cipher
        self.chunk_size = chunk_size.value

    async def receive_message(self) -> tuple[Tags, bytes]:
        is_header = True
        chunks = []
        header = b''

        while True:
            length_bytes = await self.s.readexactly(4)
            length = int.from_bytes(length_bytes, "big")
            chunk = await self.s.readexactly(min(length, self.chunk_size))

            if chunk:
                if chunk == b'MSGEND':
                    break

                # Separate header tags from message content
                if chunk == b'<!DATA>':
                    # Generate UTC timestamp on the serverside
                    timestamp = self.cipher.encrypt(str(
                            datetime.now().astimezone(UTC).timestamp()
                            ).encode())
                    chunks.append(len(timestamp).to_bytes(4, "big"))
                    chunks.append(timestamp)

                    header = b''.join(chunks)
                    chunks.clear()
                    is_header = False
                    continue

                if is_header:
                    chunks.append(length_bytes)
                chunks.append(chunk)
            else:
                raise RuntimeError("Socket connection broken")

        tags = HeaderParser(header, self.cipher).tags

        encrypted = b''.join(chunks)
        data = decrypt_message(self.cipher, encrypted)
        return tags, data
