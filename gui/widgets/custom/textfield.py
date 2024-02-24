from PySide6.QtWidgets import (
    QLineEdit, 
    QLabel, 
    QGraphicsDropShadowEffect
    )
from PySide6.QtGui import QPainter

class TextField(QLineEdit):
    def __init__(self, label: str=None, drop_shadow=None, parent=None):
        super(TextField, self).__init__(parent)
        self.label = QLabel(label)
        self.label.hide()
        self.label.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 0);
            letter-spacing: 2px;
            """)
        self.setFrame(False)
        if drop_shadow is not None:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(0)
            shadow.setColor(drop_shadow)
            self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        super(TextField, self).paintEvent(event)
        painter = QPainter(self)
        painter.drawPixmap(7, 3, self.label.grab())