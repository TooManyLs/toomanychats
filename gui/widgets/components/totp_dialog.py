from io import BytesIO

from PySide6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLineEdit)
from PySide6.QtGui import QImage, QPixmap, QRegularExpressionValidator as Q_reV
from PySide6.QtCore import Qt, QRegularExpression as Q_re
import pyotp
import qrcode
from qrcode.main import QRCode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import HorizontalBarsDrawer
from qrcode.image.styles import colormasks

from . import Dialog, TextField


class TOTPDialog(Dialog):
    def __init__(self, username: str, server_addr: str, parent) -> None:
        super().__init__(parent)
        self.username = username
        self.server = server_addr
        self.d_parent = parent
        self.setFixedWidth(370)

        # TOTP generation
        self.secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.secret)        
        uri = self.totp.provisioning_uri(
            name=f"toomanychats ({self.username}@{self.server})"
            )

        # QR code generation
        qr = QRCode(
            version=3,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=10,
            border=0,
            image_factory=StyledPilImage,
        )
        qr.add_data(uri)

        module = HorizontalBarsDrawer()
        mask = colormasks.SolidFillColorMask(
            back_color=(30, 30, 30), 
            front_color=(241, 241, 241)
        )

        img = qr.make_image(image_factory=StyledPilImage, 
                            module_drawer=module,
                            color_mask=mask)
        buffer = BytesIO()
        img.save(buffer, "PNG")
        buffer = buffer.getvalue()
        img = QImage.fromData(buffer, "PNG")
        img = QPixmap.fromImage(img)
        img = img.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, 
                   Qt.TransformationMode.SmoothTransformation)

        self.qr = QLabel()
        self.qr.setPixmap(img)

        # Text
        self.scan = QLabel("SCAN THE QR CODE")
        self.instruction = QLabel(
            "Open your authenticator app and scan QR code on the screen using your phone or enter the code below manually."
        )

        self.manual = QLabel("MANUAL ENTRY KEY")

        self.manual_key = QLineEdit()
        self.manual_key.setReadOnly(True)
        self.manual_key.setText(self.secret)

        self.verify_label = QLabel("VERIFY CODE")
        self.inv_code = QLabel()

        self.scan.setObjectName("subtitle")
        self.manual.setObjectName("subtitle")
        self.verify_label.setObjectName("subtitle")
        self.instruction.setObjectName("small")
        self.manual_key.setObjectName("small")
        self.inv_code.setObjectName("invalid")
        self.instruction.setWordWrap(True)

        # Textfield
        self.code_field = TextField("6-digit authenticator code: ", "#2e2e2e")
        self.code_field.setFixedWidth(250)
        validator = Q_reV(Q_re("[0-9]{6}"))
        self.code_field.setValidator(validator)

        # Buttons
        buttons = QHBoxLayout()

        self.cancel = QPushButton("Cancel")
        self.cancel.setFixedWidth(90)
        self.verify = QPushButton("Verify")
        self.verify.setFixedWidth(90)

        buttons.addWidget(self.cancel, alignment=Qt.AlignmentFlag.AlignLeft)
        buttons.addWidget(self.verify, alignment=Qt.AlignmentFlag.AlignRight)


        main = QVBoxLayout(self)
        main.setSpacing(0)
        main.setContentsMargins(10, 10, 10, 10)
        main.addSpacing(10)
        main.addWidget(self.qr, alignment=Qt.AlignmentFlag.AlignHCenter)
        main.addSpacing(20)
        main.addWidget(self.scan)
        main.addWidget(self.instruction)
        main.addWidget(self.manual)
        main.addWidget(self.manual_key)
        main.addWidget(self.verify_label)
        main.addSpacing(10)
        main.addWidget(self.code_field, alignment=Qt.AlignmentFlag.AlignHCenter)
        main.addWidget(self.inv_code)
        main.addLayout(buttons)

        self.cancel.clicked.connect(self.dialog_reject)
        self.verify.clicked.connect(self.verify_totp)

        self.setStyleSheet(
            """
            QPushButton{
                padding: 7px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover{
                background-color: #2e2e2e;
            }
            TextField{
                height: 30px;
                padding-top: 15px;
                padding-left: 5px;
                font-size: 16px;
                border-radius: 6px;
            }
            QLineEdit{
                outline: none;
                background-color: #1e1e1e;
                border: none;
                padding-left: 1px;
                color: white;
            }
            #subtitle{
                margin-left: 10px;
                font-size: 14px;
                font-weight: 700;
            }
            #small{
                margin-left: 11px;
                margin-bottom: 10px;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.7px;
            }
            #invalid{
                margin-top: 5px;
                margin-bottom: 5px;
                margin-left: 50px;
                color: red;
                font-size: 10px;
            }
            """
        )

    def showEvent(self, event):
        super().showEvent(event)
        parent_geometry = self.d_parent.main_window.geometry()
        self.move(parent_geometry.center() - self.rect().center())
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.verify.click()
        return super().keyPressEvent(event)

    def dialog_accept(self):
        self.d_parent.secret = self.secret.encode()
        self.d_parent.main_window.overlay.hide()
        self.close()
    
    def dialog_reject(self):
        self.d_parent.main_window.overlay.hide()
        self.close()

    def verify_totp(self) -> None:
        self.inv_code.setText("")
        otp = self.code_field.text()

        if not self.totp.verify(otp):
            self.inv_code.setText("Invalid authenticator code try again.")
            return
        self.dialog_accept()

