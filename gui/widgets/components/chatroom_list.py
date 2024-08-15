from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QSpacerItem


class ChatRoomList(QWidget):
    collapsed_width = 70
    threshold_width = 240

    def __init__(self, window) -> None:
        super().__init__()
        self.is_collapsed = False
        self.constrained_by_size = False
        self.main_window = window
        self.list = QVBoxLayout(self)
        self.list.setDirection(QVBoxLayout.Direction.BottomToTop)
        self.list.setContentsMargins(0,0,0,0)
        self.list.setSpacing(0)

        self.list.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        self.setStyleSheet("background-color: #161616;")

    def collapse_toggle(self) -> None:
        self.is_collapsed = not self.is_collapsed
        print("Collapsed" if self.is_collapsed else "Expanded")