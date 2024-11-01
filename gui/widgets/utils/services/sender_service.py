import os
from ssl import SSLSocket
from uuid import UUID
from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher
from PySide6.QtCore import QObject

from ...message import ChunkSize, Sender, MsgType

video_extensions = (".mp4", ".m4a", ".m4v", ".3gp", ".3g2", ".avi", ".mkv",
                    ".webm", ".f4v", ".lrv")

class SenderServiceWorker(QObject):
    def __init__(
            self, sock: SSLSocket, name: str, cipher: PKCS1OAEP_Cipher,
            server_pubkey: bytes, buffer_limit: ChunkSize
    ) -> None:
        super().__init__()

        self.sender_wk = Sender(
                sock, name, cipher, server_pubkey, buffer_limit
                )
        self.s_pubkey = server_pubkey

    def send_text(self, msg: bytes, public_key: bytes, room_id: UUID) -> None:
        self.sender_wk.send_message(msg, MsgType.TEXT, public_key, room_id)

    def send_static_image(
            self, data: bytes, public_key: bytes, room_id: UUID
    ) -> None:
        self.sender_wk.send_message(
                data, MsgType.IMAGE, public_key,
                room_id, basename=".jpg"
                )

    def send_file(
            self, path: str, public_key: bytes, room_id: UUID
    ) -> None:
        ext = os.path.splitext(path)[1]
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()

        if ext == ".gif":
            typ = MsgType.IMAGE
        elif ext in video_extensions:
            typ = MsgType.VIDEO
        else:
            typ = MsgType.DOCUMENT

        self.sender_wk.send_message(
                data, typ, public_key,
                room_id, filename
                )

    def send_cmd(self, cmd: bytes, room_id: UUID) -> None:
        self.sender_wk.send_message(
                cmd, MsgType.SERVER,
                self.s_pubkey, room_id
                )
