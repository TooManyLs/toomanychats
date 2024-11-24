from datetime import datetime
from enum import Enum
from uuid import UUID

from PySide6.QtCore import Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from . import EllipsisLabel
from .image_preview import ImagePreview


class ChatType(Enum):
    PRIVATE = 1
    GROUP = 2

class ChatRoomItem(QFrame):
    room_switch= Signal(bytes)
    def __init__(self, title: str, chat_type: ChatType, room_id: UUID) -> None:
        super().__init__()
        self.id = room_id
        if chat_type == ChatType.PRIVATE:
            self.picture = r"./public/private_chat.png"
        else:
            self.picture = r"./public/group_chat.png"

        self.setMinimumHeight(70)
        self.setMinimumWidth(240)

        self.time = QLabel(datetime.now().strftime("%I:%M %p"))
        self.time.setObjectName("time")

        self.hor_layout = QHBoxLayout(self)
        self.hor_layout.setContentsMargins(10, 10, 10, 10)
        self.text_layout = QVBoxLayout()
        self.text_layout.setContentsMargins(7, 0, 0, 0)

        self.pic = ImagePreview(self.picture, 50, 50, size=256)

        self.title = EllipsisLabel(title, elide="right")
        self.title.setObjectName("chat-title")
        self.t_t = QHBoxLayout()
        self.t_t.addWidget(self.title)
        self.t_t.addSpacerItem(
            QSpacerItem(
                0, 0, QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum
            )
        )
        self.t_t.addWidget(self.time, alignment=Qt.AlignmentFlag.AlignRight)
        
        # self.title.setFont(font)
        self.last_msg = EllipsisLabel(
            "There was absolutely nothing crazy written here",
            elide="right",
            bold=False
        )
        self.last_msg.setObjectName("lastmsg")

        self.text_layout.addLayout(self.t_t)
        self.text_layout.addWidget(self.last_msg)

        self.hor_layout.addWidget(self.pic)
        self.hor_layout.addLayout(self.text_layout)

        self.setObjectName("chritem")
        self.setStyleSheet(
            """
                #chritem:hover{background: #1e1e1e;}
                #chritem QLabel{background: transparent;}
                #lastmsg{
                    color: gray;
                    margin-left: -3px;
                    margin-bottom: 13px;
                }
                #time{color: gray;}
            """
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"pressed {self.title.text()}_{self.id} chat room")
            self.room_switch.emit(self.id.bytes)
        return super().mousePressEvent(event)
