import os
import platform
import subprocess
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, 
    QHBoxLayout, 
    QLineEdit,
    QLabel,
    QTextEdit, 
    QPushButton, 
    QSizePolicy,
    QFrame,
    QSpacerItem
    )
from PySide6.QtGui import (
    QFontMetrics, 
    QPainter, 
    QColor,
    QResizeEvent, 
    QTextDocument, 
    QCursor,
    QFont
    )
from PySide6.QtCore import Qt, QEvent
from .image_preview import ImagePreview

picture_type = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif")

class EllipsisLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMaximumWidth(500)
        self.counter = 0
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
                                      Qt.ElideMiddle, widgetWidth)
        
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, text)

    def resizeEvent(self, e: QResizeEvent) -> None:
        while self.counter < 1:
            self.compute_size()
            self.counter = 1
        return super().resizeEvent(e)

    def compute_size(self):
        parent_width = self.parent().parent().parent().parent().size().width()
        text_width = self.metrics.horizontalAdvance(self.text())
        if text_width > parent_width * 0.8 - 100:
            text_width = parent_width * 0.8 - 100

        self.setFixedWidth(min(text_width, 400))

class DocAttachment(QFrame):
    def __init__(self, path, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = datetime.now().strftime("%I:%M %p")
        _, ext = os.path.splitext(path)
        filename = os.path.basename(path)
        filesize = os.path.getsize(path)
        kb = filesize / 1024
        mb = kb / 1024
        gb = mb / 1024

        if gb > 1:
            filesize = f"{gb:.1f} GB"
        elif mb > 1:
            filesize = f"{mb:.1f} MB"
        elif kb > 1:
            filesize = f"{kb:.1f} KB"

        if ext in picture_type:
            self.preview = ImagePreview(path)
        else: 
            self.preview = ImagePreview("./public/document.png")
        self.path = path
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.setDirection(QVBoxLayout.Direction.BottomToTop)
        layout.setAlignment(Qt.AlignBottom)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5,5,5,5)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignTop)
        info_layout.setContentsMargins(10,0,10,0)
        self.name_text = EllipsisLabel(filename)
        size_text = QLabel(filesize)
        time_text = QLabel(self.time)
        size_text.setObjectName("secondary")
        time_text.setObjectName("secondary")

        info_layout.addWidget(self.name_text, alignment=Qt.AlignTop)
        info_layout.addWidget(size_text, alignment=Qt.AlignTop)
        info_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        info_layout.addWidget(time_text, 
                              alignment= Qt.AlignBottom | Qt.AlignRight)





        main_layout.addWidget(self.preview)
        main_layout.addLayout(info_layout)

        layout.addLayout(main_layout)
        
        self.setFixedHeight(85)
        self.setStyleSheet(
            """
            QFrame{
            background-color: #2e2e2e;
            border-radius: 12px;}
            #secondary{color: gray;};
            """
            )
        self.setCursor(QCursor(Qt.PointingHandCursor))

        if name:
            self.name = QPushButton(name)
            self.name.clicked.connect(lambda: print(f"pushed {name}"))
            name_font = self.name.font()
            name_font.setBold(True)
            self.name.setFont(name_font)
            metrics = QFontMetrics(self.font())
            self.name.setMaximumWidth(
                metrics.horizontalAdvance(self.name.text()) * 1.4)
            layout.addWidget(self.name)
            self.name.setStyleSheet("padding-left: 7px; padding-top: 2px;")
            self.setFixedHeight(103)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonRelease and isinstance(watched, QLineEdit):
            self.mouseReleaseEvent(event)
            event.accept()
            return False
        return super().eventFilter(watched, event)
    
    def mouseReleaseEvent(self, ev):
        absolute_path = os.path.abspath(self.path)
        
        if platform.system() == 'Windows':
            os.startfile(absolute_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', absolute_path))
        else:  # linux variants
            subprocess.call(('xdg-open', absolute_path))
        return super().mouseReleaseEvent(ev)