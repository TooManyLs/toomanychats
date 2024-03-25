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
    QPainter
    )

class CustomMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(150)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(1)

        self.code_btn = QPushButton("Your code")
        self.logout_btn = QPushButton("Log out")
        self.logout_btn.setObjectName("logout")

        self.layout.addWidget(self.code_btn)
        self.layout.addWidget(self.logout_btn)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        self.setStyleSheet(
            """
            QMenu{background-color: #101010;}
            QPushButton{
                border: none;
                border-radius: 0;
                padding: 7px; 
                background-color: #2e2e2e;
            }
            QPushButton:hover{background-color: #3e3e3e;}
            #logout:hover{background-color: #a03e3e;}
            """
            )

        self.logout_btn.clicked.connect(self.log_out)
        self.code_btn.clicked.connect(self.get_code)

    def log_out(self):
        parent = self.parent().parent().parent().parent()
        if parent is None:
            # for tests
            parent = self.parent().parent().parent()
        parent.initUI()

    def get_code(self):
        parent = self.parent().parent()
        try:
            parent.on_send("@get_code")
        except AttributeError:
            # for tests
            pass

    def showEvent(self, event):
        button = self.parent()
        if button is not None:
            pos = button.mapToGlobal(button.rect().bottomRight())
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