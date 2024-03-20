from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, 
    QHBoxLayout, 
    QLabel, 
    QSpacerItem, 
    QToolButton, 
    QSizePolicy,
    QMenu,
    )
from PySide6.QtGui import QIcon, QAction

class CustomMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """
            QMenu{
                border-radius: 10px;
                width: 120px;
            }
            """
            )
        
    

class ChatHeader(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QHBoxLayout(self)
        self.title = QLabel("Chat Room")
        self.options = QToolButton()
        self.options.setFixedSize(30, 30)
        self.options.setIcon(QIcon("./public/options.png"))

        self.menu = CustomMenu()
        self.menu.addAction("action")
        self.menu.addAction("action")
        self.options.setMenu(self.menu)
        self.options.setPopupMode(QToolButton.InstantPopup)

        self.layout.addItem(QSpacerItem(30, 30, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.options)
        self.layout.setContentsMargins(8,8,8,8)

        self.setStyleSheet(
            """
            QFrame{
                background-color: #161616;
                border-bottom: 1px solid #2e2e2e;
            }
            QToolButton{
                border: none;
                border-radius: 6px;
            }
            QToolButton:hover{
                background-color: #2e2e2e;
            }
            QToolButton::menu-indicator{
                image: none;
            }
            QLabel{
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            """
            )