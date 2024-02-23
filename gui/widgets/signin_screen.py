from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    )
from PySide6.QtGui import QRegularExpressionValidator as Q_reV
from PySide6.QtCore import QRegularExpression as Q_re
from widgets.utils.encryption import (
    encrypt_aes, 
    decrypt_aes, 
    generate_key, 
    send_encrypted,
    recv_encrypted
    )
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from base64 import b64decode

class SignIn(QWidget):
    def __init__(self, stacked_layout, s, server_pubkey):
        super().__init__()
        self.stacked_layout = stacked_layout
        self.s = s
        self.server_pubkey = server_pubkey

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

            self.s.send(name.encode('utf-8'))
            try:
                with open(f"keys/{name}_private.pem", "rb") as f:
                    my_pvtkey = RSA.import_key(f.read())
                my_cipher = PKCS1_OAEP.new(my_pvtkey)
                data = self.s.recv(2048).decode('utf-8')
                data, aes, pub = recv_encrypted(data)
                aes = my_cipher.decrypt(aes)
                server_resp = decrypt_aes(data, aes).decode('utf-8')
                salt, challenge = server_resp.split("|")
                key = generate_key(password, b64decode(salt.encode('utf-8')))
                response = decrypt_aes(b64decode(challenge.encode('utf-8')), key).decode('utf-8')
                if response == "OK":
                    self.s.send("OK".encode('utf-8'))
                    connected = encrypt_aes(f"{name} connected."\
                                            .encode('utf-8'))
                    self.s.send(send_encrypted(connected, self.server_pubkey).encode('utf-8'))
                    self.stacked_layout.setCurrentIndex(2)
                    return name, my_cipher
            except Exception:
                self.incorrect.setText("Failed to authenticate:\nInvalid username or password.")
            print(name, password)
        if not self.pass_f.hasAcceptableInput():
            self.inv_p.setText("Invalid password (8-50 characters)")
        if not self.name_f.hasAcceptableInput():
            self.inv_n.setText("Invalid password (3-20 characters)")
