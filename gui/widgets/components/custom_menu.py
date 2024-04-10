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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.setStyleSheet(
            """
            QMenu{background-color: #161616;}
            QPushButton{
                border: none;
                border-radius: 0;
                padding: 7px; 
                padding-right: 75px;
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

    def add_separator(self):
        self.layout.addItem(QSpacerItem(0, 1))

    def showEvent(self, event):
        parent = self.parent()
        if hasattr(parent, "options"):
            pos = parent.mapToGlobal(parent.rect().bottomRight())
            offset = QPoint(-self.width() - 7, 0)
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