from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QSpacerItem


class ChatRoomList(QWidget):
    collapsed_width = 65
    threshold_width = 240

    def __init__(self, window) -> None:
        super().__init__()
        self.is_collapsed = False
        self.main_window = window
        self.list = QVBoxLayout(self)
        self.list.setContentsMargins(0,0,0,0)
        self.list.setSpacing(0)

        self.list.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    
    def collapse_toggle(self, state: bool) -> None:
        self.is_collapsed = state
        print("Collapsed" if state else "Expanded")