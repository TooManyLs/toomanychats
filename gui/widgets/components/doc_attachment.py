import os
import platform
import subprocess
from datetime import datetime
import shutil

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit,
                               QLabel, QPushButton, QSizePolicy,
                               QFrame, QSpacerItem, QFileDialog,
                               QApplication, QWidget
                               )
from PySide6.QtGui import QFontMetrics, QCursor
from PySide6.QtCore import Qt, QEvent, QMimeData

from . import EllipsisLabel, CustomMenu
from .image_preview import ImagePreview

picture_type = ('.bmp', '.cur', '.gif', '.icns', '.ico', '.jpeg', '.jpg', 
                '.pbm', '.pgm', '.png', '.ppm', '.tga', '.tif', '.tiff', 
                '.webp', '.xbm', '.jfif', '.dds', '.cr2', '.dng', '.heic', 
                '.heif', '.jp2', '.jpe', '.jps', '.nef', '.psd', '.ras', 
                '.sgi', '.avif', '.avifs')

class DocAttachment(QFrame):
    def __init__(self, path, name=None, 
                 attachment=False, parent: QWidget | None = None,
                 timestamp: datetime = datetime.now(),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.par = parent
        self.time = timestamp.strftime("%I:%M %p")
        _, ext = os.path.splitext(path)
        self.filename = os.path.basename(path)
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
        elif str(filesize)[-1] == "1":
            filesize = f"{filesize} byte"
        else:
            filesize = f"{filesize} bytes"

        if ext.lower() in picture_type:
            self.preview = ImagePreview(path)
        else: 
            self.preview = ImagePreview("./public/document.png")
        self.path = path
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.setDirection(QVBoxLayout.Direction.BottomToTop)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5,5,5,5)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_layout.setContentsMargins(10,0,5,0)
        self.name_text = EllipsisLabel(self.filename, elide="middle")
        size_text = QLabel(filesize)
        size_text.setObjectName("secondary")

        info_layout.addWidget(self.name_text, 
                              alignment=Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(size_text, alignment=Qt.AlignmentFlag.AlignTop)
        info_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, 
                        QSizePolicy.Policy.Expanding))
        if not attachment:
            time_text = QLabel(self.time)
            time_text.setObjectName("secondary")
            info_layout.addWidget(time_text, 
                                alignment= Qt.AlignmentFlag.AlignBottom 
                                | Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(self.preview)
        main_layout.addLayout(info_layout)

        layout.addLayout(main_layout)
        
        self.setFixedHeight(85)
        self.setMinimumWidth(250)
        self.setStyleSheet(
            """
            QFrame{
            color: white;
            background-color: #2e2e2e;
            border-radius: 12px;}
            #secondary{color: gray;};
            """
            )
        if attachment:
            self.setFixedWidth(290)
            self.setStyleSheet("#secondary{color: gray;}")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        if name:
            self.name = QPushButton(name)
            self.name.setFixedHeight(23)
            main_layout.setContentsMargins(5,0,5,5)
            self.name.clicked.connect(lambda: print(f"pushed {name}"))
            name_font = self.name.font()
            name_font.setBold(True)
            self.name.setFont(name_font)
            metrics = QFontMetrics(self.font())
            self.name.setMaximumWidth(
                int(metrics.horizontalAdvance(self.name.text()) * 1.4))
            layout.addWidget(self.name)
            layout.addItem(
                QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, 
                            QSizePolicy.Policy.Minimum))
            self.name.setStyleSheet("color: white;\
                    background-color: rgba(0,0,0,0);")
            self.setFixedHeight(103)
        
        self.counter = 0

    def compute_size(self):
        if self.par:
            self.setMaximumWidth(int(min(self.par.width()*0.8, 500)))
    
    def showEvent(self, e) -> None:
        while self.counter < 1:
            self.compute_size()
            self.counter = 1
        return super().showEvent(e)

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.Type.MouseButtonRelease 
                and isinstance(watched, QLineEdit)):
            self.mouseReleaseEvent(event)
            event.accept()
            return False
        return super().eventFilter(watched, event)
    
    def mouseReleaseEvent(self, ev):
        absolute_path = os.path.abspath(self.path)
        if ev.button() == Qt.MouseButton.LeftButton:
            if self.path.lower().endswith(picture_type):
                if platform.system() == 'Windows':
                    os.startfile(absolute_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', absolute_path))
                else:  # linux variants
                    subprocess.call(('xdg-open', absolute_path))
            else:
                subprocess.Popen(f'explorer /select,"{self.path}"')
        return super().mouseReleaseEvent(ev)
    
    def contextMenuEvent(self, ev) -> None:
        self.menu = CustomMenu(self)
        self.menu.add_action("Save as", self.save_as)
        self.menu.add_action("Copy Filename", self.copy_name)
        if platform.system() != "Linux":
            self.menu.add_action("Show in Folder", self.show_in_folder)
        self.menu.add_action("Delete", lambda:self.deleteLater(), 
                        style="color: #e03e3e;")
        self.menu.exec(ev.globalPos())

    def save_as(self):
        default = os.path.basename(self.path)
        _, ext = os.path.splitext(default)
        filters = {
        '.png': 'PNG Image (*.png);;',
        '.jpg': 'JPEG Image (*.jpg *.jpeg);;',
        '.jpeg': 'JPEG Image (*.jpg *.jpeg);;',
        '.bmp': 'Bitmap Image (*.bmp);;',
        '.txt': 'Text File (*.txt);;',
        '.doc': 'Word Document (*.doc *.docx);;',
        '.docx': 'Word Document (*.doc *.docx);;',
        '.torrent': 'BitTorrent seed file (*.torrent);;',
        '.zip': 'Zip archive (*.zip, *.zipx);;',
        '.zipx': 'Zip archive (*.zip, *.zipx);;',
        }

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Document", default, 
            filter=f"{filters.get(ext, '')}All files (*.*)"
            )
        if file_name:
            shutil.copy(self.path, file_name)

    def copy_name(self):
        mime_data = QMimeData()
        mime_data.setText(self.filename)
        QApplication.clipboard().setMimeData(mime_data)

    def show_in_folder(self):
        abspath = os.path.abspath(self.path)
        if platform.system() == 'Windows':
            subprocess.Popen(f'explorer /select,"{abspath}"')
        else:
            subprocess.Popen(f'open -R "{abspath}"')
