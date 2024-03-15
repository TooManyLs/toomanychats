import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem, 
    QSizePolicy, 
    QFileDialog,
    QApplication,
    QDialog,
    )
from PySide6.QtGui import Qt, QIcon, QCursor
from PySide6.QtCore import Slot, Signal, QObject, QThread, QTimer
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from .utils.encryption import (
    encrypt_aes, 
    decrypt_aes,
    pack_data,
    unpack_data
    )
from .utils.tools import generate_name, compress_image
from .custom import TextArea
from .components import (
    TextBubble, 
    SingleImage, 
    ScrollArea, 
    DocAttachment,
    AttachDialog,
    )

class Worker(QObject):
    finished = Signal()
    message_received = Signal(bytes, bytes)

    def __init__(self, s, my_cipher, pvt):
        super().__init__()
        self.s = s
        self.my_cipher = my_cipher
        self.pub = pvt.public_key()

    @Slot()
    def run(self):
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
            except Exception:
                break
        self.finished.emit()
    
    def _receive_chunks(self, chunk_size=65536):
        chunks = []
        while True:
            chunk = self.s.recv(chunk_size)
            if chunk:
                if b'-!-END-!-' in chunk:
                    s_pos = chunk.find(b'-!-END-!-')
                    e_pos = s_pos + 9
                    chunks.append(chunk[:s_pos] + chunk[e_pos:])
                    break
                chunks.append(chunk)
            else:
                return None
        return b''.join(chunks)


class ChatWidget(QWidget):
    def __init__(self, stacked_layout, s, server_pubkey):
        super().__init__()
        self.stacked_layout = stacked_layout
        self.s = s
        self.server_pubkey = server_pubkey

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.horizontalScrollBar().setEnabled(False)

        self.chat_area = QWidget()
        self.chat_area.setObjectName("scrollarea")
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.setSpacing(5)
        self.layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)

        attach_icon = QIcon("./public/attach.png")
        self.attach = QPushButton(icon=attach_icon)
        self.button = QPushButton("Send")
        self.send_field = TextArea()
        self.send_field.setPlaceholderText("Write a message...")
        self.send_field.setObjectName("tarea")
        self.attach.setCursor(QCursor(Qt.PointingHandCursor))
        self.button.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(
            """
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
        input_layout.setContentsMargins(8,0,8,7)
        input_layout.addWidget(self.attach)
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)

        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

        self.button.clicked.connect(self.on_send)
        self.attach.clicked.connect(self.attach_file)

    def listen_for_messages(self, name):
        self.name = name
        with open(f"keys/{name}_private.pem", "rb") as f:
            my_pvtkey = RSA.import_key(f.read())
        self.my_cipher = PKCS1_OAEP.new(my_pvtkey)
        self.worker = Worker(self.s, self.my_cipher, my_pvtkey)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.message_received.connect(self.on_message_received)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    @Slot(bytes, bytes)
    def on_message_received(self, msg, ext):
        picture_type = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif")
        ext = ext.decode('utf-8')
        if ext and ext in picture_type:
            name = generate_name() + ext
            with open(f"./cache/img/{name}", "wb") as image:
                image.write(msg)
            img = SingleImage(f"./cache/img/{name}")
            img.setFocusProxy(self.send_field)
            self.layout.addWidget(img, alignment=Qt.AlignLeft)
        elif ext and ext not in picture_type:
            with open(f"./cache/attachments/{ext}", "wb") as doc:
                doc.write(msg)
            doc = DocAttachment(f"./cache/attachments/{ext}")
            doc.setFocusProxy(self.send_field)
            self.layout.addWidget(doc, alignment=Qt.AlignLeft)
        else:
            msg = msg.decode('utf-8')
            msg, nametag = msg.rsplit("|", 1)
            bubble = TextBubble(msg, nametag)
            bubble.setFocusProxy(self.send_field)
            self.layout.addWidget(bubble, alignment=Qt.AlignLeft)

    def on_send(self):
        to_send: str = self.send_field.toPlainText().strip()
        if to_send:
            bubble = TextBubble(to_send)
            bubble.setFocusProxy(self.send_field)
            self.layout.addWidget(bubble, alignment=Qt.AlignRight)
            data_to_send = encrypt_aes((to_send + f"|{self.name}").encode('utf-8'))
            self._send_chunks(pack_data(data_to_send, self.server_pubkey))
        self.send_field.clear()
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)
    
    def attach_file(self, files=None):
        if not files:
            files, _ = QFileDialog().getOpenFileNames(
                self, "Choose Files", 
                filter="All files (*.*)")
        if files:
            self.dialog = AttachDialog(self, files=files)
            self.window().overlay.show()
            self.dialog.show()

    def on_dialog_finished(self, result, files):
        self.dialog.hide()
        self.window().overlay.hide()
        if result == QDialog.Accepted:
            self.display_attach(files)

    def display_attach(self, files):
        for f, pic in files:
            if pic:
                compressed = compress_image(f)
                with open(compressed, "rb") as image:
                    data = image.read()
                    data, key = encrypt_aes(data)
                    _, ext = os.path.splitext(compressed)
                    data = (b"IMAGE:" + ext.encode('utf-8') + b'<img>' + data, key)
                    self._send_chunks(pack_data(data, self.server_pubkey))
                img = SingleImage(compressed)
                img.setFocusProxy(self.send_field)
                self.layout.addWidget(img, alignment=Qt.AlignRight)
            else:
                with open(f, "rb") as doc:
                    data = doc.read()
                    data, key = encrypt_aes(data)
                    filename = os.path.basename(f)
                    data = (b"DOCUMENT:" + filename.encode('utf-8') + b'<doc>' + data, key)
                    self._send_chunks(pack_data(data, self.server_pubkey))
                doc = DocAttachment(f)
                doc.setFocusProxy(self.send_field)
                self.layout.addWidget(doc, alignment=Qt.AlignRight)
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def _send_chunks(self, data, chunk_size=65536):
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            self.s.send(chunk)
        self.s.send(b'-!-END-!-')

    def scroll_down(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.scroll_area.old_max = scrollbar.maximum()
        self.scroll_area.relative_position = (
            scrollbar.value() / self.scroll_area.old_max
            if self.scroll_area.old_max > 0 else 0)

    def resizeEvent(self, event):
        for c in self.chat_area.children():
            if c.isWidgetType():
                try:
                    c.compute_size()
                except AttributeError:
                    c.name_text.compute_size()

    def showEvent(self, event) -> None:
        self.window().overlay.raise_()
    
    