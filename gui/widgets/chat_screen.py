from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem, 
    QSizePolicy, 
    QScrollArea, 
    )
from PySide6.QtGui import Qt
from PySide6.QtCore import Slot, Signal, QObject, QThread
from datetime import datetime
from widgets.utils.encryption import (
    encrypt_aes, 
    send_encrypted,
    decrypt_aes,
    recv_encrypted,
    )
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from widgets.custom.textfield import TextArea
from widgets.components.message_container import ChatBubble

class Worker(QObject):
    finished = Signal()
    message_received = Signal(str)

    def __init__(self, s, my_cipher):
        super().__init__()
        self.s = s
        self.my_cipher = my_cipher

    @Slot()
    def run(self):
        while True:
            try:
                data = self.s.recv(10000).decode('utf-8')
                data, aes, pub = recv_encrypted(data)
                aes = self.my_cipher.decrypt(aes)
                msg = decrypt_aes(data, aes).decode('utf-8')
                msg = msg.replace("<SEP>", ": ", 1)
                self.message_received.emit(msg)
            except Exception:
                break
        self.finished.emit()

class ChatWidget(QWidget):
    def __init__(self, stacked_layout, s, server_pubkey):
        super().__init__()
        self.stacked_layout = stacked_layout
        self.s = s
        self.server_pubkey = server_pubkey

        self.name = ""
        self.my_cipher = None

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_area = QWidget()
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.setSpacing(5)
        self.layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        main_layout = QVBoxLayout()

        self.button = QPushButton("Send")
        self.send_field = TextArea()
        self.send_field.setPlaceholderText("Write a message...")
        self.send_field.setObjectName("tarea")
        self.setStyleSheet(
            """
            #tarea{
                border: none;
            }
            """
            )

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)

        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

        self.button.clicked.connect(self.on_send)

    def listen_for_messages(self, name):
        self.name = name
        with open(f"keys/{name}_private.pem", "rb") as f:
            my_pvtkey = RSA.import_key(f.read())
        self.my_cipher = PKCS1_OAEP.new(my_pvtkey)
        self.worker = Worker(self.s, self.my_cipher)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.message_received.connect(self.on_message_received)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    @Slot(str)
    def on_message_received(self, msg):
        if msg[:8] == "[Server]":
            bubble = ChatBubble(msg)
            self.layout.addWidget(bubble, alignment=Qt.AlignLeft)
        else:
            bubble = ChatBubble(msg)
            self.layout.addWidget(bubble, alignment=Qt.AlignLeft)

    def on_send(self):
        to_send: str = self.send_field.toPlainText().strip()
        if to_send:
            bubble = ChatBubble(to_send)
            self.layout.addWidget(bubble, alignment=Qt.AlignRight)
            to_send = encrypt_aes(to_send.encode('utf-8'))
            self.s.send(send_encrypted(to_send, self.server_pubkey).encode('utf-8'))
            self.send_field.clear()
    
    