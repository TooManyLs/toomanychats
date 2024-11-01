from ssl import SSLSocket
from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher
from PySide6.QtCore import QObject, Signal, Slot

from ...message import ChunkSize, Receiver


class ReceiverServiceWorker(QObject):
    finished = Signal()
    message_received = Signal(dict, bytes)

    def __init__(
            self, sock: SSLSocket, cipher: PKCS1OAEP_Cipher,
            buffer_limit: ChunkSize
    ) -> None:
        super().__init__()

        self.receiver = Receiver(sock, cipher, buffer_limit)

    @Slot()
    def run(self) -> None:
        while True:
            try:
                tags, data = self.receiver.receive_message()
                self.message_received.emit(tags, data)
            except (RuntimeError) as e:
                print(e)
                break
        self.finished.emit()
