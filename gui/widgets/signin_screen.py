from ssl import SSLSocket

from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    )
from PySide6.QtGui import QKeyEvent, QRegularExpressionValidator as Q_reV
from PySide6.QtCore import QRegularExpression as Q_re, Signal, Qt
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey

from .utils.encryption import (
    encrypt_aes,
    decrypt_aes, 
    generate_key, 
    pack_data,
    unpack_data,
    )
from .utils.tools import get_device_id
from .components import TextField

class AuthError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SignIn(QWidget):
    name_signal = Signal(str)
    reinit = Signal()
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

        self.code_f = TextField("Code:", "#2e2e2e")
        self.verify_btn = QPushButton("Verify")
        self.inv_c = QLabel()

        self.code_f.setObjectName("text-field")
        self.verify_btn.setObjectName("signin")
        self.inv_c.setObjectName("invalid")

        valid_code = Q_reV(Q_re("[0-9]{6}"))
        self.code_f.setValidator(valid_code)

        mfa = QVBoxLayout()

        mfa.addWidget(self.code_f)
        mfa.addWidget(self.inv_c)
        mfa.addWidget(self.verify_btn)

        self.form_frame = QFrame()
        self.form_frame.setLayout(form)
        self.mfa_frame = QFrame()
        self.mfa_frame.setLayout(mfa)
        self.mfa_frame.hide()

        layout.addWidget(self.form_frame, 1, 1)
        layout.addWidget(self.mfa_frame, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnMinimumWidth(1, 300)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.setStyleSheet(
            """
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
        self.verify_btn.clicked.connect(self.verify_totp)

        self.shown_btn = self.btn

    def sign_in(self):
        self.inv_n.setText("")
        self.inv_p.setText("")
        self.incorrect.setText("")
        if (self.pass_f.hasAcceptableInput()
                and self.name_f.hasAcceptableInput()):
            name = self.name_f.text()
            password = self.pass_f.text()
            name_device = f"{name}<SEP>".encode() + get_device_id(name) 
            self.s.send(
                pack_data(encrypt_aes(name_device),
                self.server_pubkey.export_key())
            )
            data = self.s.recv(2048)
            try:
                self.new = False
                if data == b"new device":
                    self.new = True
                    self.my_pvtkey = RSA.generate(2048)
                    my_pubkey = self.my_pvtkey.public_key().export_key()
                    self.s.send(my_pubkey)
                    data = self.s.recv(2048)
                else:
                    with open(f"keys/{name}_private.pem", "rb") as f:
                        self.my_pvtkey = RSA.import_key(f.read())
                my_cipher = PKCS1_OAEP.new(self.my_pvtkey)
                
                data, aes, _ = unpack_data(data)
                aes = my_cipher.decrypt(aes)
                server_resp = decrypt_aes(data, aes)
                salt, challenge = server_resp.split(b"<SEP>")
                key = generate_key(password, salt)
                check_bytestring = decrypt_aes(challenge, key)
                self.s.send(check_bytestring)
                resp = self.s.recv(6)
                if resp != b"passed":
                    raise AuthError

                self.form_frame.hide()
                self.shown_btn = self.verify_btn
                self.mfa_frame.show()
                self.code_f.setFocus()

            except ValueError:
                self.s.send(b"failed")
                self.s.recv(6)
                self.incorrect.setText(
                    "Failed to authenticate:\nInvalid password.")
            except (FileNotFoundError, AuthError):
                self.incorrect.setText(
                    "Failed to authenticate:\nInvalid username or password.")
        if not self.pass_f.hasAcceptableInput():
            self.inv_p.setText("Invalid password (8-50 characters)")
        if not self.name_f.hasAcceptableInput():
            self.inv_n.setText("Invalid name (3-20 characters)")

    def verify_totp(self):
        self.inv_c.setText("")
        if not self.code_f.hasAcceptableInput():
            self.inv_c.setText("Authentication code should be 6 digits long.")
            return
        name = self.name_f.text()
        otp = self.code_f.text()
        otp_key = otp.rjust(32, "0").encode()
        encrypted, _ = encrypt_aes(otp.encode(), key=otp_key)
        self.s.send(encrypted)
        resp = self.s.read(6)
        if resp == b"failed":
            self.inv_c.setText("The code is wrong")
            return
        elif resp == b"passed":
            if self.new:
                with open(f"keys/{name}_private.pem", "wb") as f:
                    f.write(self.my_pvtkey.export_key())
        else:
            # Too many attempts 
            self.reinit.emit()
            return

        self.stacked_layout.setCurrentIndex(3)
        self.name_signal.emit(name)
        for f in self.fields:
            f.clear()
    
    def sign_up(self):
        for f in self.fields:
                f.clear()
        self.s.send("/signup".encode())
        self.stacked_layout.setCurrentIndex(2)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Return:
            self.shown_btn.click()
        return super().keyPressEvent(event)
