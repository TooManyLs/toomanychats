from typing import Callable

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QPushButton, 
    QMenu,
    QSpacerItem
    )
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QKeySequence,
    QShortcut
    )

class CustomMenu(QMenu):
    def __init__(self, parent=None, offset=False):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.offset = offset

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint 
            | Qt.WindowType.Popup 
            | Qt.WindowType.NoDropShadowWindowHint
        )

        self.menu_layout = QVBoxLayout(self)
        self.menu_layout.setContentsMargins(0,0,0,0)
        self.menu_layout.setSpacing(0)

        self.setStyleSheet(
            """
            QMenu{background-color: rgba(0,0,0,0);}
            QPushButton{
                border: none;
                border-radius: 0;
                padding: 7px; 
                background-color: #3e3e3e;
                text-align: left;
                color: white;
            }
            QPushButton:hover{background-color: #4e4e4e;}
            QPushButton:disabled{color: #6e6e6e;}
            #danger:hover{background-color: #a03e3e;}
            """
            )
        
        self.h = 0

    def add_action(self, text: str, action: Callable=None, *, 
                   obj_name: str=None, style: str=None, 
                   shortcut: str=None, status: bool=True) -> None:
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
### status:
Disables/enables button depending on value(default: True - enabled).
        """
        self.btn = QPushButton(text)
        self.h += 30
        self.btn.setObjectName(obj_name)
        self.menu_layout.addWidget(self.btn)
        self.btn.clicked.connect(action)
        self.btn.clicked.connect(self.close)
        self.btn.setEnabled(status)
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

    def add_separator(self):
        spacer_height = 2
        self.menu_layout.addItem(QSpacerItem(0, spacer_height))
        self.h += spacer_height

    def showEvent(self, event):
        parent = self.parent()
        if hasattr(parent, "options"):
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            offset = QPoint(-self.width() - 7, 0)
            self.move(pos + offset)
        elif self.offset: 
            pos = self.window().mapToParent(self.window().rect().topRight())
            offset = QPoint(-self.width() - 170, 0)
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
