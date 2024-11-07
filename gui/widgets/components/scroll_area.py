from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QScrollArea

class ScrollArea(QScrollArea):
    def __init__(self, color: str = "#1e1e1e", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verticalScrollBar().rangeChanged.connect(self.handleRangeChanged)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.horizontalScrollBar().setEnabled(False)
        self.old_max = self.verticalScrollBar().maximum()
        self.relative_position = self.verticalScrollBar().value() / self.old_max if self.old_max > 0 else 0
        self.setStyleSheet(
            """
            QScrollArea{
                background-color: """ + color + """;
                border: none;
            }
            QScrollBar:vertical {
                width: 7px;
                background-color: transparent;
                border: none;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical
            {
                border-image: url(:/qss_icons/rc/down_arrow_disabled.png);
            }
            QScrollBar::handle:vertical {
                background: #5e5e5e;
                min-height: 20px;
                border-radius: 2px;
                margin: 5px 3px 5px 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: none;
            }
            """
            )
        self.verticalScrollBar().setVisible(False)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_scrollbar)

    def wheelEvent(self, arg__1):
        self.verticalScrollBar().setVisible(True)
        self.hide_timer.start(1500)

        self.old_max = self.verticalScrollBar().maximum()
        self.relative_position = self.verticalScrollBar().value() / self.old_max if self.old_max > 0 else 0
        super().wheelEvent(arg__1)

    def handleRangeChanged(self, min, max):
        if self.old_max != max and self.old_max > 0:
            new_value = self.relative_position * max
            self.verticalScrollBar().setValue(new_value)
        self.old_max = max

    def enterEvent(self, event) -> None:
        self.verticalScrollBar().setVisible(True)
        self.hide_timer.start(1500)
        return super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.hide_timer.start(1500)
        return super().leaveEvent(event)

    def _hide_scrollbar(self) -> None:
        self.verticalScrollBar().setVisible(False)
