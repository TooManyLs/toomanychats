import os
import subprocess
import platform
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout,  
    QSizePolicy,
    QLabel,
    )
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QCursor, 
    QPainter,  
    QPixmap, 
    QImageReader, 
    QMovie, 
    QPainterPath,
    )

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
        
        if ev.button() == Qt.LeftButton:
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
        pw = max(pixmap.width(), 100)
        aspect_ratio = pixmap.height() / pixmap.width()
        new_width = min(parent_width * 0.8, 500, pw)
        new_height = new_width * aspect_ratio

        if new_height > 600:
            new_height = 600
            new_width = new_height / aspect_ratio

        self.setFixedSize(new_width, new_height)

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

            pixmap = pixmap.scaled(
                self.frameSize(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()), 12, 12)
            painter.setClipPath(path)
            painter.drawPixmap(self.rect(), pixmap)
            painter.end()