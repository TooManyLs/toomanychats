from ssl import SSLSocket

from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    )
from PySide6.QtGui import QRegularExpressionValidator as Q_reV
from PySide6.QtCore import QRegularExpression as Q_re, Signal
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey

from .utils.encryption import (
    decrypt_aes, 
    generate_key, 
    unpack_data
    )
from .components import TextField

class AuthError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SignIn(QWidget):
    name_signal = Signal(str)
    def __init__(self, stacked_layout, s: SSLSocket | None,
                 server_pubkey: RsaKey | None):
        super().__init__()
        if s is None or server_pubkey is None:
            return
        self.stacked_layout = stacked_layout
        self.s = s
        self.server_pubkey = server_pubkey

        layout = QGridLayout()

        self.name_f = TextField("Username:", "#2e2e2e")
        self.pass_f = TextField("Password:", "#2e2e2e", True)
        self.btn = QPushButton("Sign in")
        self.reg = QPushButton("Don't have an account yet? Sign up.")
        self.inv_n = QLabel()
        self.inv_p = QLabel()
        self.incorrect = QLabel()
        self.name_f.setObjectName("text-field")
        self.pass_f.setObjectName("text-field")
        self.inv_n.setObjectName("invalid")
        self.inv_p.setObjectName("invalid")
        self.incorrect.setObjectName("invalid")
        self.btn.setObjectName("signin")
        self.reg.setObjectName("reg")

        valid_name = Q_reV(Q_re("[a-zA-Z0-9_]{3,20}"))
        valid_pass = Q_reV(Q_re("^.{8,50}$"))
        self.name_f.setValidator(valid_name)
        self.pass_f.setValidator(valid_pass)

        form = QVBoxLayout()

        form.addWidget(self.name_f)
        form.addWidget(self.inv_n)

        form.addWidget(self.pass_f)
        form.addWidget(self.inv_p)

        form.addWidget(self.btn)
        form.addWidget(self.incorrect)
        form.addWidget(self.reg)

        layout.addItem(form, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnMinimumWidth(1, 300)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.setStyleSheet(
            """
            QPushButton{outline: none;}
            #signin{
                background-color: #2e2e2e;
                height: 45px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
            }
            #signin:hover{background-color: #3e3e3e;}
            #signin:pressed{background-color: #5e5e5e;}
            #reg{
                border: none;
                color: #888888;
            }
            #reg:hover{color: #f1f1f1;}
            #invalid{
                margin-top: 5px;
                margin-bottom: 5px;
                color: red;
                font-size: 10px;
            }
            #text-field{
            height: 30px;
            padding-top: 15px;
            padding-left: 5px;
            font-size: 16px;
            border-radius: 6px;
            }
            """
            )
        self.fields = self.findChildren(TextField)

        for w in self.fields:
            w.setMaximumWidth(400)

        self.btn.clicked.connect(self.sign_in)
        self.reg.clicked.connect(self.sign_up)

    def sign_in(self):
        self.inv_n.setText("")
        self.inv_p.setText("")
        self.incorrect.setText("")
        if (self.pass_f.hasAcceptableInput()
                and self.name_f.hasAcceptableInput()):
            name = self.name_f.text()
            password = self.pass_f.text()
            self.s.send(name.encode())
            data = self.s.recv(2048)
            try:
                try:
                    if data.decode() == "failed":
                        raise AuthError
                except UnicodeDecodeError:
                    pass
                with open(f"keys/{name}_private.pem", "rb") as f:
                    my_pvtkey = RSA.import_key(f.read())
                my_cipher = PKCS1_OAEP.new(my_pvtkey)
                
                data, aes, pub = unpack_data(data)
                aes = my_cipher.decrypt(aes)
                server_resp = decrypt_aes(data, aes)
                salt, challenge = server_resp.split(b"<SEP>")
                key = generate_key(password, salt)
                response = decrypt_aes(challenge, key)
                if response == b"OK":
                    self.s.send(b"OK")
                    for f in self.fields:
                        f.clear()
                    self.stacked_layout.setCurrentIndex(3)
                    if self.s.read(7) == b"success":
                        self.name_signal.emit(name)
            except ValueError:
                self.s.send(b"Fail")
                self.incorrect.setText(
                    "Failed to authenticate:\nInvalid username or password.")
            except (FileNotFoundError, AuthError):
                self.incorrect.setText(
                    "Failed to authenticate:\nInvalid username or password.")
        if not self.pass_f.hasAcceptableInput():
            self.inv_p.setText("Invalid password (8-50 characters)")
        if not self.name_f.hasAcceptableInput():
            self.inv_n.setText("Invalid name (3-20 characters)")
    
    def sign_up(self):
        for f in self.fields:
                f.clear()
        self.s.send("/signup".encode())
        self.stacked_layout.setCurrentIndex(2)
