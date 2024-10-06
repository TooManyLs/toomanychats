import os
from ssl import SSLSocket
from threading import Thread
from time import sleep

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QSpacerItem, QSizePolicy,
                               QFileDialog, QApplication, QDialog,
                               QFrame
                               )
from PySide6.QtGui import Qt, QIcon, QCursor, QImage
from PySide6.QtCore import Slot, Signal, QObject, QThread, QTimer, QMimeData
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher
from PIL import UnidentifiedImageError

from .utils.encryption import (
    encrypt_aes, 
    decrypt_aes,
    pack_data,
    unpack_data,
    )
from .utils.tools import compress_image, qimage_to_bytes, generate_name
from .components import (TextBubble, SingleImage, ScrollArea,
                         DocAttachment,AttachDialog,ChatHeader,
                         TextArea, VideoWidget)

class Worker(QObject):
    finished = Signal()
    message_received = Signal(bytes, bytes)

    def __init__(self, s: SSLSocket, my_cipher: PKCS1OAEP_Cipher, pvt: RsaKey):
        super().__init__()
        self.s = s
        self.my_cipher = my_cipher
        self.pub = pvt.public_key()

    @Slot()
    def run(self) -> None:
        while True:
            try:
                data = self._receive_chunks()
                data, aes, pub = unpack_data(data)
                header = b''
                if data[:6] == b'IMAGE:':
                    header, data = data.split(b'<img>')
                    header = header[6:]
                elif data[:9] == b'DOCUMENT:':
                    header, data = data.split(b'<doc>')
                    header = header[9:]
                aes = self.my_cipher.decrypt(aes)
                msg = decrypt_aes(data, aes)
                self.message_received.emit(msg, header)
                del msg, data, aes, pub, header
            except (OSError, ValueError):
                print("disconnect")
                break
        self.finished.emit()

    def _receive_chunks(self, chunk_size: int = 65536) -> bytes:
        data_length = int.from_bytes(self.s.recv(4), 'big')
        chunks = []
        bytes_read = 0
        while bytes_read < data_length:
            chunk = self.s.recv(min(chunk_size, data_length - bytes_read))
            if chunk:
                chunks.append(chunk)
                bytes_read += len(chunk)
            else:
                raise RuntimeError("Socket connection broken")
        return b''.join(chunks)


class ChatWidget(QWidget):
    def __init__(self, s: SSLSocket | None, 
                 server_pubkey: RsaKey | None, window):
        super().__init__()
        if s is None or server_pubkey is None:
            return
        self.s = s
        self.server_pubkey = server_pubkey.export_key()
        self.main_window = window

        self.scroll_area = ScrollArea()

        self.chat_area = QWidget()
        self.chat_area.setObjectName("scrollarea")
        self.scroll_area.setWidget(self.chat_area)

        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setSpacing(5)
        self.chat_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, 
                        QSizePolicy.Policy.Expanding))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        attach_icon = QIcon("./public/attach.png")
        self.attach = QPushButton(attach_icon, "")
        self.button = QPushButton("Send")
        self.send_field = TextArea()
        self.send_field.attach.connect(self.attach_file)
        self.send_field.send.connect(self.on_send)
        self.send_field.setPlaceholderText("Write a message...")
        self.send_field.setObjectName("tarea")
        self.attach.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        inputs = QFrame()
        inputs.setObjectName("inputs")
        self.setStyleSheet(
            """
            #inputs{
                background-color: #161616;
            }
            QPushButton{
                border: none;
                border-radius: 6px;
                padding: 7px;
                outline: none;
                }
            QPushButton:hover{
                background-color: #2e2e2e;
            }
            #tarea{
                border: none;
            }
            #scrollarea{
                background-color: #1e1e1e;
            }     
            """
            )
        self.scroll_area.setFocusProxy(self.send_field)
        self.attach.setFocusProxy(self.send_field)
        self.button.setFocusProxy(self.send_field)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(7,7,7,7)
        input_layout.addWidget(self.attach)
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)
        inputs.setLayout(input_layout)

        self.header = ChatHeader()
        self.header.getCode.connect(self.on_send)

        main_layout.addWidget(self.header)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(inputs)

        self.setLayout(main_layout)

        self.button.clicked.connect(self.on_send)
        self.attach.clicked.connect(self.attach_file)

    def listen_for_messages(self, name: str) -> None:
        self.name = name
        with open(f"keys/{name}_private.pem", "rb") as f:
            my_pvtkey = RSA.import_key(f.read())
        self.my_cipher = PKCS1_OAEP.new(my_pvtkey)
        self.worker = Worker(self.s, self.my_cipher, my_pvtkey)
        self.wk_thread = QThread()
        self.worker.moveToThread(self.wk_thread)
        self.worker.finished.connect(self.wk_thread.quit)
        self.worker.message_received.connect(self.on_message_received)
        self.wk_thread.started.connect(self.worker.run)
        self.wk_thread.start()

    @Slot(bytes, bytes)
    def on_message_received(self, msg: bytes, header: bytes) -> None:
        picture_type = (".jpg", ".gif")
        ext = header.decode()
        if ext in picture_type:
            if ext == ".jpg":
                path = QImage.fromData(msg)
            else:
                path = f"./cache/img/{generate_name()}.gif"
                with open(path, 'wb') as file:
                    file.write(msg)
            img = SingleImage(path)
            img.setFocusProxy(self.send_field)
            self.chat_layout.addWidget(img, 
                                       alignment=Qt.AlignmentFlag.AlignLeft)
        elif ext and ext not in picture_type:
            path = f"./cache/attachments/{ext}"
            with open(path, 'wb') as file:
                file.write(msg)
            if ext[-4:] == ".mp4":
                doc = VideoWidget(path, self)
            else:
                doc = DocAttachment(f"./cache/attachments/{ext}", parent=self)
            doc.setFocusProxy(self.send_field)
            self.chat_layout.addWidget(doc, 
                                       alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            txt = msg.decode()
            try:
                txt, nametag = txt.rsplit("|", 1)
            except ValueError:
                mime_data = QMimeData()
                mime_data.setText(txt)
                QApplication.clipboard().setMimeData(mime_data)
                print("copied")
                return
            bubble = TextBubble(txt, nametag)
            bubble.sel = self.send_field
            bubble.chat = self.chat_area
            self.chat_layout.addWidget(bubble, 
                                       alignment=Qt.AlignmentFlag.AlignLeft)
            
    def on_send(self, cmd: str = "") -> None:
        if cmd == "@get_code":
            self.s.send("code".encode())
            return
        to_send: str = self.send_field.toPlainText().strip()     
        if to_send:
            bubble = TextBubble(to_send)
            bubble.sel = self.send_field
            bubble.chat = self.chat_area
            self.chat_layout.addWidget(bubble, 
                                       alignment=Qt.AlignmentFlag.AlignRight)
            data_to_send = encrypt_aes((to_send + f"|{self.name}").encode())
            self._send_chunks(pack_data(data_to_send, self.server_pubkey))
        self.send_field.clear()
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)
    
    def attach_file(self, files: list[str] | None):
        if not files:
            files, _ = QFileDialog().getOpenFileNames(
                self, "Choose Files", 
                filter="All files (*.*)")
        if files:
            try:
                self.dialog = AttachDialog(files, self)
            except UnidentifiedImageError:
                return
            self.main_window.overlay.show()
            self.dialog.show()

    def on_dialog_finished(self, result: QDialog.DialogCode, 
                           files: list[tuple[str, bool]]) -> None:
        self.dialog.hide()
        self.main_window.overlay.hide()
        if result == QDialog.DialogCode.Accepted:
            self.display_attach(files)

    def display_attach(self, files: list[tuple[str, bool]]) -> None:
        for f, pic in files:
            if pic:
                _, ext = os.path.splitext(f)
                if ext != ".gif":
                    compressed = compress_image(f)
                    args = (compressed, True)
                else:
                    args = (f, True)
                attachment = SingleImage(f)
            else:
                args = (f, False)
                if os.path.splitext(f)[1] == ".mp4":
                    attachment = VideoWidget(f, self)
                else:
                    attachment = DocAttachment(f, parent=self)
            self.t = Thread(target=self._send_file, args=args)
            self.t.start()
            attachment.setFocusProxy(self.send_field)
            self.chat_layout.addWidget(attachment, 
                                       alignment=Qt.AlignmentFlag.AlignRight)
            sleep(0.05)
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def _send_file(self, f: str | QImage, is_pic: bool) -> None:
        if isinstance(f, QImage):
            data = qimage_to_bytes(f)
        else:
            with open(f, "rb") as file:
                data = file.read()

        data, key = encrypt_aes(data)
        
        if is_pic or isinstance(f, QImage):
            ext = ".jpg" if isinstance(f, QImage) else ".gif"
            data = (b"IMAGE:" + ext.encode() + b'<img>' + data, key)
        else:
            filename = os.path.basename(f)
            data = (b"DOCUMENT:" + filename.encode() + b'<doc>' + data, key)
        self._send_chunks(pack_data(data, self.server_pubkey))

    def _send_chunks(self, data: bytes, chunk_size: int = 65536) -> None:
        self.s.sendall(len(data).to_bytes(4, 'big'))
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            self.s.sendall(chunk)

    def scroll_down(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.scroll_area.old_max = scrollbar.maximum()
        self.scroll_area.relative_position = (
            scrollbar.value() / self.scroll_area.old_max
            if self.scroll_area.old_max > 0 else 0)

    def resizeEvent(self, event):
        if hasattr(self, 'dialog'):
            self.dialog.update_geometry()
            event.accept()
        for c in self.chat_area.children():
            if c.isWidgetType():
                # All widgets in "chat_area" should be resizable
                # so we assume that "c" has "compute_size" attribute
                c.compute_size() #type: ignore
  