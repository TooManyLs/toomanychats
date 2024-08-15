from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QRectF, QRect
from PySide6.QtGui import (
    QCursor, 
    QPainter, 
    QPixmap, 
    QImageReader, 
    QPainterPath,
    QTransform, 
    )

from ..utils.tools import compress_image

class ImagePreview(QLabel):
    def __init__(self, path, h=75, w=75, radius=9.5, size=128, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.radius = radius
        self.h = h
        self.w = w
        if path == "./public/document.png":
            self.path = path
            image_reader = QImageReader(self.path)
            image_reader.setAutoTransform(True)
            image = image_reader.read()
        else:
            image = compress_image(path, size)
        pixmap = QPixmap.fromImage(image)
        self.setPixmap(pixmap)
        self._pixmap = pixmap
        self._resized = False
        self.setScaledContents(False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(w, h)

        self.counter = 0

    def setPixmap(self, arg__1):
        if not arg__1:
            return
        self._pixmap = arg__1
    
    def paintEvent(self, arg__1):
        super().paintEvent(arg__1)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)
        painter.setClipPath(path)

        crop_size = min(self._pixmap.width(), self._pixmap.height())

        image = self._pixmap.toImage()
        transform = QTransform()
        transform = transform.scale(self.w / crop_size, self.h / crop_size)
        image = image.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        pixmap = QPixmap.fromImage(image)

        center_x = (pixmap.width() - self.w) // 2
        center_y = (pixmap.height() - self.h) // 2

        painter.drawPixmap(self.rect(), pixmap, QRect(center_x, center_y, self.w, self.h))
        painter.end()