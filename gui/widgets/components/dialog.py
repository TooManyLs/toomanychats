from PySide6.QtWidgets import QDialog, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import (QPainter, QPainterPath, QBrush, 
                           QPen, QColor)

class Dialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 12, 12)
        painter.fillPath(path, QBrush(QColor("#1e1e1e")))
        painter.strokePath(path, QPen(Qt.PenStyle.NoPen))