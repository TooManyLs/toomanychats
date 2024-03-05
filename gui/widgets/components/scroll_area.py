from PySide6.QtWidgets import QScrollArea

class ScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verticalScrollBar().rangeChanged.connect(self.handleRangeChanged)
        self.old_max = self.verticalScrollBar().maximum()
        self.relative_position = self.verticalScrollBar().value() / self.old_max if self.old_max > 0 else 0

    def wheelEvent(self, event):
        self.old_max = self.verticalScrollBar().maximum()
        self.relative_position = self.verticalScrollBar().value() / self.old_max if self.old_max > 0 else 0
        super().wheelEvent(event)

    def handleRangeChanged(self, min, max):
        if self.old_max != max and self.old_max > 0:
            new_value = self.relative_position * max
            self.verticalScrollBar().setValue(new_value)
        self.old_max = max
