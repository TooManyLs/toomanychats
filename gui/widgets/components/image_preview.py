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
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path == "./public/document.png":
            self.path = path
        else:
            self.path = compress_image(path, 128, gif_compression=True)
        image_reader = QImageReader(self.path)
        image_reader.setAutoTransform(True)
        image = image_reader.read()
        pixmap = QPixmap.fromImage(image)
        self.setPixmap(pixmap)
        self._pixmap = pixmap
        self._resized = False
        self.setScaledContents(False)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(75, 75)

        self.counter = 0

    def setPixmap(self, arg__1):
        if not arg__1:
            return
        self._pixmap = arg__1
    
    def paintEvent(self, arg__1):
        super().paintEvent(arg__1)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 9.5, 9.5)
        painter.setClipPath(path)

        crop_size = min(self._pixmap.width(), self._pixmap.height())

        image = self._pixmap.toImage()
        transform = QTransform()
        transform = transform.scale(75 / crop_size, 75 / crop_size)
        image = image.transformed(transform, Qt.SmoothTransformation)
        pixmap = QPixmap.fromImage(image)

        center_x = (pixmap.width() - 75) // 2
        center_y = (pixmap.height() - 75) // 2

        painter.drawPixmap(self.rect(), pixmap, QRect(center_x, center_y, 75, 75))
        painter.end()