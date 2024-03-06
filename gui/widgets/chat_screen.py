from base64 import b64decode, b64encode
from datetime import datetime
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
    )
from PySide6.QtGui import Qt, QIcon
from PySide6.QtCore import Slot, Signal, QObject, QThread, QTimer
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from .utils.encryption import (
    encrypt_aes, 
    decrypt_aes,
    pack_data,
    unpack_data
    )
from .utils.tools import generate_name
from .custom import TextArea
from .components import TextBubble, SingleImage, ScrollArea

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
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.setSpacing(5)
        self.layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        main_layout = QVBoxLayout()

        attach_icon = QIcon("./public/attach.png")
        self.attach = QPushButton(icon=attach_icon)
        self.button = QPushButton("Send")
        self.send_field = TextArea()
        self.send_field.setPlaceholderText("Write a message...")
        self.send_field.setObjectName("tarea")
        self.setStyleSheet(
            """
            QPushButton{
                border: none;
                outline: none;
                }
            #tarea{
                border: none;
            }
            """
            )

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.attach)
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)

        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

        self.button.clicked.connect(self.on_send)
        self.attach.clicked.connect(self.attach_files)

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
        if ext:
            name = generate_name() + ext.decode('utf-8')
            with open(f"./cache/img/{name}", "wb") as image:
                image.write(msg)
            img = SingleImage(f"./cache/img/{name}")
            self.layout.addWidget(img, alignment=Qt.AlignLeft)
        else:
            msg = msg.decode('utf-8')
            msg, nametag = msg.rsplit("|", 1)
            bubble = TextBubble(msg, nametag)
            self.layout.addWidget(bubble, alignment=Qt.AlignLeft)
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def on_send(self):
        to_send: str = self.send_field.toPlainText().strip()
        if to_send:
            bubble = TextBubble(to_send)
            self.layout.addWidget(bubble, alignment=Qt.AlignRight)
            data_to_send = encrypt_aes((to_send + f"|{self.name}").encode('utf-8'))
            self._send_chunks(pack_data(data_to_send, self.server_pubkey))
        self.send_field.clear()
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def attach_files(self):
        files, filter = QFileDialog().getOpenFileNames(
            self, "Choose files",
            filter="Image files (*.jpg *.png *.bmp *.webp *.gif)")
        for f in files:
            with open(f, "rb") as image:
                data = image.read()
                data, key = encrypt_aes(data)
                _, ext = os.path.splitext(f)
                data = (b"IMAGE:" + ext.encode('utf-8') + b'<img>' + data, key)
                self._send_chunks(pack_data(data, self.server_pubkey))
            img = SingleImage(f)
            self.layout.addWidget(img, alignment=Qt.AlignRight)
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
                c.compute_size()
    
    