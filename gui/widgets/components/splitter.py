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
        sizes = self.sizes()
        sidebar_width = sizes[0]
        collapsed_width = self.main_window.chat_room_list_widget.collapsed_width
        threshold_width = self.main_window.chat_room_list_widget.threshold_width
        collapse_point = collapsed_width * 2

        if sidebar_width < threshold_width:
            if sidebar_width > collapse_point:
                self.setSizes([threshold_width, self.width() - threshold_width])
                if self.main_window.chat_room_list_widget.is_collapsed:
                    self.main_window.chat_room_list_widget.collapse_toggle(False)
            else:
                self.setSizes([collapsed_width, sizes[1] + (sidebar_width - collapsed_width)])
                if not self.main_window.chat_room_list_widget.is_collapsed:
                    self.main_window.chat_room_list_widget.collapse_toggle(True)