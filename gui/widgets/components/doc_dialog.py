from PySide6.QtWidgets import (
    QDialog, 
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    )
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class Overlay(QWidget):
    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)
        self.setPalette(QColor(0, 0, 0, 120))
        self.setAutoFillBackground(True)

class PopupDialog(QDialog):
    def __init__(self, parent=None, files=None):
        super(PopupDialog, self).__init__(parent)
        self.data = files
        print(self.data)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setGeometry(0, 0, 350, 400)

        main = QVBoxLayout(self)
        main.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.cancel = QPushButton("Cancel")
        self.send = QPushButton("Send")
        self.cancel.setFixedWidth(60)
        self.send.setFixedWidth(60)
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.cancel, alignment=Qt.AlignRight)
        button_layout.addWidget(self.send, alignment=Qt.AlignRight)

        main.addLayout(button_layout, 1)

        self.setStyleSheet(
            """
            QPushButton{
                padding: 7px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover{
                background-color: #2e2e2e
                }
            """
            )

        self.cancel.clicked.connect(self.reject)
        self.send.clicked.connect(self.accept)

    def showEvent(self, event):
        parent_geometry = self.parent().geometry()
        self.move(parent_geometry.center() - self.rect().center())