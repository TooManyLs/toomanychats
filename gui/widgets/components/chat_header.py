from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
)

from .custom_menu import CustomMenu


class ChatHeader(QFrame):
    reinit = Signal()
    getCode = Signal(str)
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.p = parent
        self.main = QHBoxLayout(self)
        self.title = QLabel("Chat Room")
        self.options = QToolButton()
        self.options.setFixedSize(30, 30)
        self.options.setIcon(QIcon("./public/options.png"))

        self.menu = CustomMenu(self)
        self.menu.add_action("Your code", self.get_code) 
        self.menu.add_action("Clear chat", self.clear_chat, 
                             style="color: #e03e3e;")
        self.menu.add_separator()
        self.menu.add_action("Log out", lambda: self.reinit.emit(), 
                             obj_name="danger", shortcut="Ctrl+Q")

        self.options.setMenu(self.menu)
        self.options.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.main.addItem(QSpacerItem(30, 30, QSizePolicy.Policy.Fixed, 
                                        QSizePolicy.Policy.Fixed))
        self.main.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main.addWidget(self.options)
        self.main.setContentsMargins(7,7,7,7)

        self.setStyleSheet(
            """
            QFrame{
                background-color: #161616;
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

    def get_code(self):
        self.getCode.emit("@get_code")
        self.menu.close()

    def clear_chat(self):
        widgets = self.p.chat_area.children()[1:]

        for w in widgets:
            w.deleteLater()
        self.menu.close()
