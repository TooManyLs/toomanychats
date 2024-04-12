import os
import subprocess
import platform
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout,  
    QSizePolicy,
    QLabel,
    QFileDialog,
    QApplication
    )
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QCursor, 
    QPainter,  
    QPixmap, 
    QImageReader, 
    QMovie,
    )

from .custom_menu import CustomMenu
from ..utils.tools import compress_image, generate_name

class SingleImage(QLabel):
    def __init__(self, path="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path
        if not path:
            self.image = compress_image()
            self._pixmap = QPixmap.fromImage(self.image)
            self.setPixmap(self._pixmap)
        else:
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

    def check_path(self):
        if not self.path:
            self.path = f"./cache/img/{generate_name()}.jpg"
            self._pixmap.save(self.path)

    def mouseReleaseEvent(self, ev):
    
        if ev.button() == Qt.LeftButton:
            self.check_path()
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
        pw = max(pixmap.width(), 100)
        aspect_ratio = pixmap.height() / pixmap.width()
        new_width = min(parent_width * 0.8, 500, pw)
        new_height = new_width * aspect_ratio

        if new_height > 600:
            new_height = 600
            new_width = new_height / aspect_ratio

        self.setFixedSize(new_width, new_height)

        mask = QPixmap(self.size())
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.black)
        painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.end()
        self.setMask(mask.mask())

    def resizeEvent(self, event):
        while self.counter < 1:
            self.compute_size()
            self.counter = 1
            self.layout.addWidget(self.time_text, 
                         alignment=Qt.AlignBottom | Qt.AlignRight)
        return super().resizeEvent(event)
    
    def contextMenuEvent(self, ev) -> None:
        self.menu = CustomMenu(self)
        self.menu.add_action("Save as", self.save_as)
        self.menu.add_action("Copy Image", self.copy)
        self.menu.add_action("Show in Folder", self.show_in_folder, 
                             status=bool(self.path))
        self.menu.add_action("Delete", lambda:self.deleteLater(), 
                        style="color: #e03e3e;")
        self.menu.exec(ev.globalPos())

    def save_as(self):
        if self.path:
            default = os.path.basename(self.path)
        else:
            default = generate_name() + ".jpg"
        _, ext = os.path.splitext(default)
        filters = {
            ".jpg": "JPEG Image (*.jpg)",
            ".gif": "GIF Image (*.gif)"
                   }
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Image", default, 
            filter=f"{filters[ext]};;All files (*.*)"
            )
        if file_name:
            if self.path:
                shutil.copy(self.path, file_name)
            else:
                self._pixmap.save(file_name)
                self.path = file_name
    
    def copy(self):
        clipboard = QApplication.clipboard()
        image = QPixmap.toImage(self._pixmap.currentPixmap()
                                if self.path.endswith(".gif") and self.path 
                                else self._pixmap)
        clipboard.setImage(image)
    
    def show_in_folder(self):
        abspath = os.path.abspath(self.path)
        subprocess.Popen(f'explorer /select,"{abspath}"')