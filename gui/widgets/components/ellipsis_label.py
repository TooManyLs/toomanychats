from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFontMetrics, QPainter, Qt


class EllipsisLabel(QLabel):
    elide_mode = {
        "middle": Qt.TextElideMode.ElideMiddle,
        "right": Qt.TextElideMode.ElideRight
    }
    def __init__(self, *args, elide: str, bold: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = elide
        self.setMaximumWidth(500)
        if bold:
            font = self.font()
            font.setBold(True)
            self.setFont(font)
        self.metrics = QFontMetrics(self.font())

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        textWidth = metrics.horizontalAdvance(self.text())
        widgetWidth = self.width()

        if textWidth <= widgetWidth:
            text = self.text()
        else:
            text = metrics.elidedText(self.text(), 
                                      self.elide_mode[self.mode], 
                                      widgetWidth)
        
        painter.drawText(self.rect(), 
                         Qt.AlignmentFlag.AlignLeft 
                         | Qt.AlignmentFlag.AlignVCenter, 
                         text)
