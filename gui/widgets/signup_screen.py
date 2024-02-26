import os
import time
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame
    )
from PySide6.QtGui import QRegularExpressionValidator as Q_reV, QIcon
from PySide6.QtCore import QRegularExpression as Q_re
from Crypto.PublicKey import RSA
from widgets.utils.encryption import (
    encrypt_aes, 
    generate_key, 
    send_encrypted,
    )
from widgets.custom.textfield import TextField
from base64 import b64encode

class SignUp(QWidget):
    def __init__(self, stacked_layout, s, server_pubkey):
        super().__init__()
        self.stacked_layout = stacked_layout
        self.s = s
        self.server_pubkey = server_pubkey

        self.main_layout = QGridLayout()
        self.back = QGridLayout()
        self.back_btn = QPushButton()
        self.back_btn.setIcon(QIcon("./public/arrow.png"))
        self.back.addWidget(self.back_btn, 0, 0)
        self.back.setColumnStretch(0, 1)
        self.back.setColumnStretch(1, 1)
        self.back.setColumnStretch(2, 1)
        self.back.setRowStretch(0, 1)
        self.back.setRowStretch(2, 1)
        self.back_btn.setObjectName("back")

        self.friend_code = TextField("Friend code", "#2e2e2e")
        self.friend_name = TextField("Friend username", "#2e2e2e")
        self.check_btn = QPushButton("Check")
        self.inv_code = QLabel()

        self.friend_code.setObjectName("text-field")
        self.friend_name.setObjectName("text-field")
        self.check_btn.setObjectName("btn")
        self.inv_code.setObjectName("invalid")


        self.name_f = TextField("Username:", "#2e2e2e")
        self.pass_f = TextField("Password:", "#2e2e2e", True)
        self.pass_confirm = TextField("Confirm password:", "#2e2e2e", True)
        self.btn = QPushButton("Sign up")
        self.inv_n = QLabel()
        self.inv_p = QLabel()
        self.inv_confirm = QLabel()
        self.inv_taken = QLabel()

        self.name_f.setObjectName("text-field")
        self.pass_f.setObjectName("text-field")
        self.pass_confirm.setObjectName("text-field")
        self.inv_n.setObjectName("invalid")
        self.inv_p.setObjectName("invalid")
        self.inv_confirm.setObjectName("invalid")
        self.inv_taken.setObjectName("invalid")
        self.btn.setObjectName("btn")

        valid_name = Q_reV(Q_re("[a-zA-Z0-9_]{3,20}"))
        valid_pass = Q_reV(Q_re("^.{8,50}$"))
        self.name_f.setValidator(valid_name)
        self.pass_f.setValidator(valid_pass)

        self.code = QVBoxLayout()
        self.code.addWidget(self.friend_code)
        self.code.addSpacing(20)
        self.code.addWidget(self.friend_name)
        self.code.addSpacing(20)
        self.code.addWidget(self.check_btn)
        self.code.addWidget(self.inv_code)

        self.form = QVBoxLayout()
        self.form.addWidget(self.name_f)
        self.form.addWidget(self.inv_n)
        self.form.addWidget(self.pass_f)
        self.form.addWidget(self.inv_p)
        self.form.addWidget(self.pass_confirm)
        self.form.addWidget(self.inv_confirm)
        self.form.addWidget(self.btn)
        self.form.addWidget(self.inv_taken)

        self.code_frame = QFrame()
        self.code_frame.setLayout(self.code)
        self.form_frame = QFrame()
        self.form_frame.setLayout(self.form)
        self.form_frame.hide()
        
        self.main_layout.addWidget(self.code_frame, 1, 1)
        self.main_layout.addWidget(self.form_frame, 1, 1)
        self.main_layout.addItem(self.back, 0, 0, -1, 1)

        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnStretch(2, 1)
        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setRowStretch(2, 1)

        self.setLayout(self.main_layout)

        self.setStyleSheet(
            """
            QPushButton{outline: none;}
            #btn{
                background-color: #2e2e2e;
                height: 45px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
            }
            #btn:hover{background-color: #3e3e3e;}
            #btn:pressed{background-color: #5e5e5e;}
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
            #back{
                border: none;
                height: 45px;
                border-radius: 6px;
            }
            #back:hover{background-color: #2e2e2e;}
            #back:pressed{background-color: #5e5e5e;}
            """
            )
        self.fields = self.findChildren(TextField)
        
        self.btn.clicked.connect(self.signup)
        self.check_btn.clicked.connect(self.check_code)
        self.back_btn.clicked.connect(self.go_back)

    def go_back(self):
        self.s.send("c".encode('utf-8'))
        self.form_frame.hide()
        self.code_frame.show()
        for f in self.fields:
            f.clear()
        self.stacked_layout.setCurrentIndex(0)
    
    def check_code(self):
        self.inv_code.setText("")
        self.s.send("/signup".encode('utf-8'))
        time.sleep(0.1)
        friend_code = "|".join([self.friend_code.text(), self.friend_name.text()])
        self.s.send(friend_code.encode('utf-8'))
        resp = self.s.recv(1024).decode('utf-8')
        if resp == "approve":
            for f in self.fields:
                f.clear()
            self.code_frame.hide()
            self.form_frame.show()
        else:
            self.inv_code.setText("Invalid friend code.")

    def signup(self):
        self.inv_n.setText("")
        self.inv_p.setText("")
        self.inv_confirm.setText("")
        self.inv_taken.setText("")

        name = self.name_f.text()
        password = self.pass_f.text()
        confirm = self.pass_confirm.text()
        
        if (self.name_f.hasAcceptableInput() 
            and self.pass_f.hasAcceptableInput() 
            and password == confirm):
            salt = os.urandom(16)
            hash = generate_key(password, salt)
            rsa_keys = RSA.generate(2048)
            pubkey = rsa_keys.public_key().export_key()
            pvtkey = rsa_keys.export_key()
            data = encrypt_aes(f"{name}|{b64encode(hash).decode('utf-8')}|\
{b64encode(salt).decode('utf-8')}|\
{pubkey.decode('utf-8')}".encode('utf-8'))
            self.s.send(send_encrypted(data, self.server_pubkey).encode('utf-8'))
            ok = self.s.recv(1024).decode('utf-8')
            if "[+]" in ok:
                with open(f"keys/{name}_private.pem", "wb") as f:
                    f.write(pvtkey)
            else:
                self.inv_taken.setText(f"This username ({name}) is already taken.")
                return
            for f in self.fields:
                f.clear()
            self.stacked_layout.setCurrentIndex(1)
        if password != confirm:
            self.inv_confirm.setText("Passwords do not match.")
        if not self.name_f.hasAcceptableInput():
            self.inv_n.setText("Invalid name (3-20 characters)")
        if not self.pass_f.hasAcceptableInput():
            self.inv_p.setText("Invalid password (8-50 characters)")