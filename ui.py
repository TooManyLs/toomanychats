import atexit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QLabel, 
    QLineEdit,
    QHBoxLayout,
    QStackedLayout,
    QGridLayout,
    )
from PySide6.QtGui import QRegularExpressionValidator as Q_reV
from PySide6.QtCore import QRegularExpression as Q_re
from encryption import (
    encrypt_aes, 
    decrypt_aes, 
    generate_key, 
    send_encrypted,
    recv_encrypted
    )
from datetime import datetime
import socket
from base64 import b64decode, b64encode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import sys

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002

# s = socket.socket()

class EnterWidget(QWidget):
    def __init__(self, stacked_layout):
        super().__init__()
        self.stacked_layout = stacked_layout

        layout = QGridLayout()

        self.sign_in_button = QPushButton("Sign In")
        self.sign_up_button = QPushButton("Sign Up")
        buttons = QVBoxLayout()
        buttons.addWidget(self.sign_in_button)
        buttons.addSpacing(20)
        buttons.addWidget(self.sign_up_button)
        layout.addItem(buttons, 1, 1)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 2)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.sign_in_button.clicked.connect(self.on_sign_in_clicked)
        self.sign_up_button.clicked.connect(self.on_sign_up_clicked)

    def on_sign_in_clicked(self):
        # name, my_cipher = signin()
        self.stacked_layout.setCurrentIndex(1)

    def on_sign_up_clicked(self):
        # name, my_cipher = signup()
        self.stacked_layout.setCurrentIndex(2)

class SignIn(QWidget):
    def __init__(self, stacked_layout):
        super().__init__()
        self.stacked_layout = stacked_layout

        layout = QGridLayout()

        self.name_l = QLabel("Name:")
        self.name_f = QLineEdit()
        self.pass_l = QLabel("Password:")
        self.pass_f = QLineEdit()
        self.btn = QPushButton("Sign in")
        self.inv_n = QLabel()
        self.inv_n.setStyleSheet("color: red")
        self.inv_p = QLabel()
        self.inv_p.setStyleSheet("color: red")
        self.incorrect = QLabel()
        self.incorrect.setStyleSheet("color: red")

        valid_name = Q_reV(Q_re("[a-zA-Z0-9_]{3,20}"))
        valid_pass = Q_reV(Q_re("^.{8,50}$"))
        self.name_f.setValidator(valid_name)
        self.pass_f.setValidator(valid_pass)

        form = QVBoxLayout()

        form.addWidget(self.name_l)
        form.addWidget(self.name_f)
        form.addWidget(self.inv_n)
        form.addWidget(self.pass_l)
        form.addWidget(self.pass_f)
        form.addWidget(self.inv_p)
        form.addSpacing(10)
        form.addWidget(self.btn)
        form.addSpacing(10)
        form.addWidget(self.incorrect)

        layout.addItem(form, 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.btn.clicked.connect(self.sign_in)

    def sign_in(self):
        self.inv_n.setText("")
        self.inv_p.setText("")
        if self.pass_f.hasAcceptableInput() and self.name_f.hasAcceptableInput():
            name = self.name_f.text()
            password = self.pass_f.text()

            s.send(name.encode('utf-8'))
            try:
                with open(f"keys/{name}_private.pem", "rb") as f:
                    my_pvtkey = RSA.import_key(f.read())
                my_cipher = PKCS1_OAEP.new(my_pvtkey)
                data = s.recv(2048).decode('utf-8')
                data, aes, pub = recv_encrypted(data)
                aes = my_cipher.decrypt(aes)
                server_resp = decrypt_aes(data, aes).decode('utf-8')
                salt, challenge = server_resp.split("|")
                key = generate_key(password, b64decode(salt.encode('utf-8')))
                response = decrypt_aes(b64decode(challenge.encode('utf-8')), key).decode('utf-8')
                if response == "OK":
                    s.send("OK".encode('utf-8'))
                    connected = encrypt_aes(f"{name} connected."\
                                            .encode('utf-8'))
                    s.send(send_encrypted(connected, server_pubkey).encode('utf-8'))
                    self.stacked_layout.setCurrentIndex(2)
                    return name, my_cipher
            except Exception:
                self.incorrect.setText("Failed to authenticate:\nInvalid username or password.")
            print(name, password)
        if not self.pass_f.hasAcceptableInput():
            self.inv_p.setText("Invalid password (8-50 characters)")
        if not self.name_f.hasAcceptableInput():
            self.inv_n.setText("Invalid password (3-20 characters)")


class ChatWidget(QWidget):
    def __init__(self, stacked_layout):
        super().__init__()
        self.stacked_layout = stacked_layout

        layout = QVBoxLayout()

        self.label = QLabel()
        self.button = QPushButton("Send")
        self.send_field = QLineEdit()

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)

        layout.addWidget(self.label)
        layout.addLayout(input_layout)

        self.setLayout(layout)

        self.button.clicked.connect(self.on_send)

    def on_send(self):
        now = datetime.now()
        date = now.strftime("%m/%d/%Y")
        time = now.strftime("%I:%M %p")

        to_send = self.send_field.text()
        if to_send:
            print(date, "at", time, to_send)

            self.send_field.clear()

class MainWindow(QMainWindow):
    global s, server_pubkey
    s = socket.socket()
    print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}")
    s.connect((SERVER_HOST, SERVER_PORT))
    server_pubkey = RSA.import_key(s.recv(1024))
    print("[+] Connected.")
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TooManyChats")

        self.stacked_layout = QStackedLayout()

        # Create the sign in widget and the main widget
        self.enter_widget = EnterWidget(self.stacked_layout)
        self.sign_in = SignIn(self.stacked_layout)
        self.main_widget = ChatWidget(self.stacked_layout)

        # Add the widgets to the QStackedLayout
        self.stacked_layout.addWidget(self.enter_widget)    # 0
        self.stacked_layout.addWidget(self.sign_in)         # 1
        self.stacked_layout.addWidget(self.main_widget)     # 2

        # Create a container widget to hold the stacked layout
        container = QWidget()
        container.setLayout(self.stacked_layout)

        # Set the container widget as the central widget
        self.setCentralWidget(container)

        atexit.register(self.quit)

    def quit(self):
        s.close()

app = QApplication(sys.argv)
app.setStyle("Fusion")

window = MainWindow()
window.resize(700, 800)
window.show()

app.exec()