import os
import subprocess
import platform
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout,  
    QSizePolicy,
    QLabel,
    )
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QPainter, QBrush, QPixmap, QImageReader, QMovie

class SingleImage(QLabel):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path
        if path[-4:] == ".gif":
            mov = QMovie(path)
            self.setMovie(mov)
            mov.start()
            self._pixmap = mov
        else:
            image_reader = QImageReader(path)
            image_reader.setAutoTransform(True)
            image = image_reader.read()

            pixmap = QPixmap.fromImage(image)
            self.setPixmap(pixmap)
            self._pixmap = pixmap
        self._resized = False
        self.setScaledContents(True)
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
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5,5,5,5)
        
        self.counter = 0

    def mouseReleaseEvent(self, ev):
        absolute_path = os.path.abspath(self.path)
        
        if platform.system() == 'Windows':
            os.startfile(absolute_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', absolute_path))
        else:  # linux variants
            subprocess.call(('xdg-open', absolute_path))
        return super().mouseReleaseEvent(ev)

    def compute_size(self):
        if isinstance(self._pixmap, QMovie):
            pixmap = self._pixmap.currentPixmap()
        else:
            pixmap = self._pixmap
        parent_width = self.parent().parent().parent().size().width()
        aspect_ratio = pixmap.height() / pixmap.width()
        self.setFixedWidth(min(parent_width * 0.85, 
                               500, 
                               pixmap.width()))
        self.setFixedHeight(self.width() * aspect_ratio)

    def resizeEvent(self, event):
        while self.counter < 1:
            self.compute_size()
            self.counter = 1
            self.layout.addWidget(self.time_text, 
                         alignment=Qt.AlignBottom | Qt.AlignRight)
        return super().resizeEvent(event)

    def setPixmap(self, arg__1):
        if not arg__1:
            return
        self._pixmap = arg__1
    
    def paintEvent(self, arg__1):
        super().paintEvent(arg__1)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if isinstance(self._pixmap, QMovie):
            pixmap = self._pixmap.currentPixmap()
        else:
            pixmap = self._pixmap

            brush = QBrush(pixmap.scaled(
                self.frameSize(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation))
            rect = self.rect()
            painter.setBrush(brush)
            painter.drawRoundedRect(rect, 12, 12)