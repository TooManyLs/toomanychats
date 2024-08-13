from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QSplitter
)

class Splitter(QSplitter):
    def __init__(self, window, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.main_window = window

        self.setHandleWidth(0)
        self.splitterMoved.connect(self.on_splitter_moved)
    
    def on_splitter_moved(self, pos, index):
        collapsed_width = self.main_window.chat_room_list_widget.collapsed_width
        threshold_width = self.main_window.chat_room_list_widget.threshold_width
        collapse_point = collapsed_width * 2

        if pos <= threshold_width:
            if pos > collapse_point and self.main_window.width() >= 640:
                self.setSizes([threshold_width, self.width() - threshold_width])
                if self.main_window.chat_room_list_widget.is_collapsed:
                    self.main_window.chat_room_list_widget.collapse_toggle()
            else:
                self.setSizes([collapsed_width, self.width() - collapsed_width])
                if not self.main_window.chat_room_list_widget.is_collapsed:
                    self.main_window.chat_room_list_widget.collapse_toggle()