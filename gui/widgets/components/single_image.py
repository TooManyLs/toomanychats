from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout,  
    QSizePolicy,
    QLabel,
    )
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QPainter, QBrush

class SingleImage(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pixmap = self.pixmap()
        self._resized = False
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.time = datetime.now().strftime("%I:%M %p")
        self.time_text = QLabel(self.time)
        self.time_text.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.time_text.setStyleSheet(
            """
            background-color: rgba(0,0,0,0.4);
            padding: 3px;
            color: white;
            border-radius: 10px;
            """
            )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        layout.addWidget(self.time_text, 
                         alignment=Qt.AlignBottom | Qt.AlignRight)

    def mouseReleaseEvent(self, ev):

        return super().mouseReleaseEvent(ev)

    def compute_size(self):
        parent_width = self.parent().parent().parent().size().width()
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        self.setFixedWidth(min(parent_width * 0.85, 
                               500, 
                               self._pixmap.width()))
        self.setFixedHeight(self.width() * aspect_ratio)

    def setPixmap(self, arg__1):
        if not arg__1:
            return
        self._pixmap = arg__1
    
    def paintEvent(self, arg__1):
        self.compute_size()
        super().paintEvent(arg__1)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        brush = QBrush(self._pixmap.scaled(
            self.frameSize(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation))
        rect = self.rect()
        painter.setBrush(brush)
        painter.drawRoundedRect(rect, 12, 12)