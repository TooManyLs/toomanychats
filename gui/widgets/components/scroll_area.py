from PySide6.QtWidgets import QScrollArea

class ScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verticalScrollBar().rangeChanged.connect(self.handleRangeChanged)
        self.old_max = self.verticalScrollBar().maximum()
        self.relative_position = self.verticalScrollBar().value() / self.old_max if self.old_max > 0 else 0
        self.setStyleSheet(
            """
            QScrollArea{
                border: none;
            }
            QScrollBar:vertical {
                width: 9px;
                background-color: #1e1e1e;
                margin-right: 5px;
            }
            QScrollBar::handle:vertical {
                background: #5e5e5e;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: #1e1e1e;
            }
            """
            )

    def wheelEvent(self, event):
        self.old_max = self.verticalScrollBar().maximum()
        self.relative_position = self.verticalScrollBar().value() / self.old_max if self.old_max > 0 else 0
        super().wheelEvent(event)

    def handleRangeChanged(self, min, max):
        if self.old_max != max and self.old_max > 0:
            new_value = self.relative_position * max
            self.verticalScrollBar().setValue(new_value)
        self.old_max = max
