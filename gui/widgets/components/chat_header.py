from typing import Callable

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QFrame, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QSpacerItem, 
    QToolButton, 
    QPushButton, 
    QSizePolicy,
    QMenu
    )
from PySide6.QtGui import (
    QIcon, 
    QPixmap,
    QPainter,
    QKeySequence,
    QShortcut
    )

class CustomMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(1)

        self.setStyleSheet(
            """
            QMenu{background-color: #101010;}
            QPushButton{
                border: none;
                border-radius: 0;
                padding: 7px; 
                background-color: #2e2e2e;
                text-align: left;
            }
            QPushButton:hover{background-color: #3e3e3e;}
            #danger:hover{background-color: #a03e3e;}
            """
            )

    def add_action(self, text: str, action: Callable, *, 
                   obj_name: str="", style: str="", 
                   shortcut: str=None) -> None:
        """
Creates button and sets action on click.
## Args:
### text: 
Text displayed on button.
### action: 
Method that runs when button is clicked.
### obj_name:
Sets object name to choose default style from CustomMenu class.
- ##### "danger" - button turns red on hover.
### style:
Sets custom stylesheet provided in QSS format.
### shortcut:
Binds key sequence to run an action that've been set to button.
        """
        self.btn = QPushButton(text)
        self.btn.setObjectName(obj_name)
        self.layout.addWidget(self.btn)
        self.btn.clicked.connect(action)
        if not obj_name:
            self.btn.setStyleSheet(style)
        
        layout = QHBoxLayout(self.btn)
        if shortcut: 
            sc_label = QLabel(shortcut)
            sc_label.setStyleSheet(
                """
                color: #7e7e7e; 
                font-size: 10px; 
                background: none;
                """
                )
            layout.addWidget(sc_label, alignment=Qt.AlignRight)
            self.scut = QShortcut(QKeySequence(shortcut), self.parent())
            self.scut.setContext(Qt.ApplicationShortcut)
            self.scut.activated.connect(action)

    def showEvent(self, event):
        parent = self.parent()
        if hasattr(parent, "options"):
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            offset = QPoint(-self.width() - 8, 0)
            self.move(pos + offset)

        mask = QPixmap(self.size())
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.black)
        painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.end()

        self.setMask(mask.mask())    

class ChatHeader(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QHBoxLayout(self)
        self.title = QLabel("Chat Room")
        self.options = QToolButton()
        self.options.setFixedSize(30, 30)
        self.options.setIcon(QIcon("./public/options.png"))
        

        self.menu = CustomMenu(self)
        self.menu.add_action("Your code", self.get_code) 
        self.menu.add_action("Log out", self.log_out, obj_name="danger", 
                             shortcut="Ctrl+Q")
        self.options.setMenu(self.menu)
        self.options.setPopupMode(QToolButton.InstantPopup)

        self.layout.addItem(QSpacerItem(30, 30, QSizePolicy.Policy.Fixed, 
                                        QSizePolicy.Policy.Fixed))
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

    def get_code(self):
        parent = self.parent()
        try:
            parent.on_send("@get_code")
        except AttributeError:
            # for tests
            print("get code")
        self.menu.close()

    def log_out(self):
        parent = self.parent().parent().parent()
        if parent is None:
            # for tests
            parent = self.parent().parent()
        parent.initUI()