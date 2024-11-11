import os
import subprocess
import platform
import shutil
from datetime import datetime
from pathlib import Path
import tempfile

from PySide6.QtWidgets import (
    QPushButton, QVBoxLayout,  QSizePolicy,
    QLabel, QFileDialog, QApplication, QWidget,
    )
from PySide6.QtCore import Qt, QMimeData, QUrl, QPoint
from PySide6.QtGui import (
    QCursor, QPainter, QPixmap, 
    QMovie, QDrag, QImage
    )

from .custom_menu import CustomMenu
from ..utils.tools import compress_image, generate_name, CLIENT_DIR

images_dir = Path(f"{CLIENT_DIR}/downloads/images")
images_dir.mkdir(parents=True, exist_ok=True)

class SingleImage(QLabel):
    def __init__(
            self, parent: QWidget, path: QImage | str = "", name: str = "",
            timestamp: datetime | None = None, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.p = parent
        self.name = name
        self.temp_file = None
        self.path = path if isinstance(path, str) else ""
        if not path:
            self.image = compress_image()
            self._pixmap = QPixmap.fromImage(self.image)
            self.setPixmap(self._pixmap)
        else:
            if self.path[-4:] == ".gif":
                mov = QMovie(path)
                self.setMovie(mov)
                mov.start()
                self._pixmap = mov
            else:
                if not isinstance(path, QImage):
                    self.image = compress_image(path)
                else:
                    self.image = path
                self._pixmap = QPixmap.fromImage(self.image)
                self.setPixmap(self._pixmap)
        self._resized = False
        self.setScaledContents(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.time = (timestamp if timestamp
                     else datetime.now()).strftime("%I:%M %p")
        self.time_text = QLabel(self.time)
        self.time_text.setSizePolicy(QSizePolicy.Policy.Minimum,
                                     QSizePolicy.Policy.Minimum)
        self.time_text.setStyleSheet(
            """
            background-color: rgba(0,0,0,0.4);
            padding: 3px;
            border-radius: 10px;
            """
            )
        if self.name:
            self.name_text = QPushButton(self.name)
            self.name_text.clicked.connect(lambda: print(f"pushed {self.name}"))
            self.name_text.setSizePolicy(QSizePolicy.Policy.Minimum,
                                         QSizePolicy.Policy.Minimum)
            self.name_text.setStyleSheet(
                """
                background-color: rgba(0,0,0,0.4);
                padding: 3px 5px;
                font-weight: 700;
                border-radius: 10px;
                """
                )
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5,5,5,5)
        
        self.counter = 0

    def check_path(self):
        if not self.path and not isinstance(self._pixmap, QMovie):
            self.path = f"{images_dir}/{generate_name()}.webp"
            self._pixmap.save(self.path)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = ev.pos()

    def mouseMoveEvent(self, ev):
        if not (ev.buttons() & Qt.MouseButton.LeftButton):
            return
        if ((ev.pos() - self.drag_start_position).manhattanLength()
            < QApplication.startDragDistance()
        ):
            return
        drag = QDrag(self)
        mime_data = QMimeData()

        if not os.path.exists(self.path) and isinstance(self._pixmap, QImage):
            self.temp_file = tempfile.NamedTemporaryFile(
                delete=False, delete_on_close=True, suffix=".webp"
            )
            self._pixmap.save(self.temp_file.name, "WEBP")
            self.path = self.temp_file.name
        else:
            self.path = os.path.abspath(self.path)

        mime_data.setUrls([QUrl.fromLocalFile(self.path)])

        scaled_pixmap = self.pixmap().scaled(
            128, 128, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

        drag.setMimeData(mime_data)
        drag.setPixmap(scaled_pixmap)
        hotspot = QPoint(
            int(scaled_pixmap.width() * 1.5),
            scaled_pixmap.height()
        )
        drag.setHotSpot(
            hotspot - QPoint(scaled_pixmap.width(),
            int(scaled_pixmap.height() * 0.5))
        )
        drag.exec_(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, ev):
        if self.temp_file:
            self.temp_file.close()
            self.temp_file = None
            self.path = ""
    
        if ev.button() == Qt.MouseButton.LeftButton:
            self.check_path()
            absolute_path = os.path.abspath(self.path)
            print(absolute_path)

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
        parent_width = self.p.size().width()
        pw = max(pixmap.width(), 100)
        aspect_ratio = pixmap.height() / pixmap.width()
        new_width = min(parent_width * 0.8, 500, pw)
        new_height = new_width * aspect_ratio

        if new_height > 600:
            new_height = 600
            new_width = new_height / aspect_ratio

        self.setFixedSize(int(new_width), int(new_height))

        mask = QPixmap(self.size())
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.end()
        self.setMask(mask.mask())

    def resizeEvent(self, event):
        while self.counter < 1:
            self.compute_size()
            self.counter = 1
            if self.name:
                self.main_layout.addWidget(self.name_text,
                             alignment=Qt.AlignmentFlag.AlignTop
                             | Qt.AlignmentFlag.AlignLeft)
            self.main_layout.addWidget(self.time_text, 
                         alignment=Qt.AlignmentFlag.AlignBottom
                                 | Qt.AlignmentFlag.AlignRight)
        return super().resizeEvent(event)
    
    def contextMenuEvent(self, ev) -> None:
        self.menu = CustomMenu(self)
        self.menu.add_action("Save as", self.save_as)
        self.menu.add_action("Copy Image", self.copy)
        if platform.system() != "Linux":
            self.menu.add_action("Show in Folder", self.show_in_folder, 
                                 status=bool(self.path))

        self.menu.add_action("Delete", lambda:self.deleteLater(), 
                        style="color: #e03e3e;")
        self.menu.exec(ev.globalPos())

    def save_as(self):
        if self.path.endswith(".gif"):
            default = os.path.basename(self.path)
        else:
            default = generate_name() + ".webp"
        _, ext = os.path.splitext(default)
        filters = {
            ".webp": "WebP Image (*.webp)",
            ".gif": "GIF Image (*.gif)"
                   }
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Image", default, 
            filter=f"{filters[ext]};;All files (*.*)"
            )
        if file_name:
            if isinstance(self._pixmap, QMovie):
                shutil.copy(self.path, file_name)
            else:
                self._pixmap.save(file_name, "WEBP")
                self.path = file_name
    
    def copy(self):
        clipboard = QApplication.clipboard()
        pixmap: QPixmap = (self._pixmap.currentPixmap()
                           if isinstance(self._pixmap, QMovie)
                           else self._pixmap)
        image = QPixmap.toImage(pixmap)
        clipboard.setImage(image)
    
    def show_in_folder(self):
        abspath = os.path.abspath(self.path)
        if platform.system() == 'Windows':
            subprocess.Popen(f'explorer /select,"{abspath}"')
        else:
            subprocess.Popen(f'open -R "{abspath}"')
