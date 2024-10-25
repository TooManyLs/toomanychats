from PySide6.QtCore import Qt, QRegularExpression as Q_re
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpacerItem, QSizePolicy, QLabel,
    )
from PySide6.QtGui import QRegularExpressionValidator as Q_reV

from . import TextField, Dialog

class ServerDialog(Dialog):
    def __init__(self, server_list, parent) -> None:
        super().__init__(parent)
        self.server_list = server_list
        self.d_parent = parent

        self.setGeometry(0, 0, 370, 200)

        main = QVBoxLayout(self)
        main.setSpacing(10)

        self.server_addr = TextField("Server address:", "#2e2e2e")
        self.server_name = TextField("Server name: (optional)", "#2e2e2e")
        self.inv_addr = QLabel("")
        self.inv_name = QLabel("")
        self.inv_addr.setObjectName("invalid")
        self.inv_name.setObjectName("invalid")

        main.addWidget(self.server_addr)
        main.addWidget(self.inv_addr)
        main.addWidget(self.server_name)
        main.addWidget(self.inv_name)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.cancel = QPushButton("Cancel")
        self.add = QPushButton("Add && connect")
        self.conn = QPushButton("Connect")
        self.cancel.setFixedWidth(110)
        self.add.setFixedWidth(110)
        self.conn.setFixedWidth(110)
        button_layout.addItem(QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Minimum))
        button_layout.addWidget(self.cancel, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self.add, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self.conn, alignment=Qt.AlignmentFlag.AlignRight)

        main.addLayout(button_layout, 1)

        # regular expression for address validation in format:
        #255.255.255.255:(1024 - 65535)
        regexp = (
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}" +
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + 
            r"\:(102[4-9]|10[3-9]\d|1[1-9]\d{2}|[2-9]\d{3}|" + 
            r"[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$"
            )

        address_validator = Q_reV(Q_re(regexp))
        self.server_addr.setValidator(address_validator)

        self.setStyleSheet(
            """
            TextField{
                height: 30px;
                padding-top: 15px;
                padding-left: 5px;
                font-size: 16px;
                border-radius: 6px;
            }
            TextField:hover{background-color: #3e3e3e;}
            TextField:pressed{background-color: #5e5e5e;}
            QPushButton{
                height: 20px;
                padding: 7px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                color: white;
            }
            QPushButton:hover{
                background-color: #3e3e3e;
                }
            #invalid{
                margin-top: 5px;
                margin-bottom: 5px;
                color: red;
                font-size: 10px;
            }
            """
            )
        
        self.cancel.clicked.connect(self.dialog_reject)
        self.add.clicked.connect(lambda: self.dialog_accept(add=True))
        self.conn.clicked.connect(self.dialog_accept)

    def dialog_accept(self, add=False):
        self.inv_addr.setText("")
        self.inv_name.setText("")
        
        name = self.server_name.text()

        valid_addr = self.server_addr.hasAcceptableInput()
        uniq = name not in self.server_list and "current" not in name.lower()

        if valid_addr and uniq:
            addr = self.server_addr.text()

            self.d_parent._on_dialog_finished(
                Dialog.DialogCode.Accepted, [addr, name], add)
        if not valid_addr:
            self.inv_addr.setText("Invalid address")
        if not uniq:
            self.inv_name.setText("Server with this name already exists")

    def dialog_reject(self):
        self.d_parent._on_dialog_finished(Dialog.DialogCode.Rejected)
