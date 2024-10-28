import os
import tempfile
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QSpacerItem, QSizePolicy, 
                               QLabel,  QCheckBox,  QApplication,
                               )
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (QColor, QDragEnterEvent, QPixmap, 
                           QMovie,)

from .scroll_area import ScrollArea
from .doc_attachment import DocAttachment
from . import Dialog
from ..utils.tools import compress_image

picture_type = ('.bmp', '.cur', '.gif', '.icns', '.ico', '.jpeg', '.jpg', 
                '.pbm', '.pgm', '.png', '.ppm', '.tga', '.tif', '.tiff', 
                '.webp', '.xbm', '.jfif', '.dds', '.cr2', '.dng', '.heic', 
                '.heif', '.jp2', '.jpe', '.jps', '.nef', '.psd', '.ras', 
                '.sgi', '.avif', '.avifs')

class Overlay(QWidget):
    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)
        self.setPalette(QColor(0, 0, 0, 120))
        self.setAutoFillBackground(True)

class AttachDialog(Dialog):
    def __init__(self, files: list[str], parent):
        super().__init__(parent)
        self.data = files
        self.d_parent = parent

        self.setGeometry(0, 0, 350, 400)

        main = QVBoxLayout(self)
        main.setSpacing(10)

        self.scroll_area = ScrollArea("#1e1e1e")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_area.setWidget(self.scroll_contents)
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(0,0,0,10)


        self.attachments: list[tuple[QWidget, str, bool]] = []
        for file in self.data:
            if file.lower().endswith(picture_type):
                label = self.set_image(file)
                self.scroll_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                self.attachments.append((label, file, True))
            else:
                doc = DocAttachment(file, attachment=True)
                self.scroll_layout.addWidget(doc, alignment=Qt.AlignmentFlag.AlignCenter)
                self.attachments.append((doc, file, False))

        main.addWidget(self.scroll_area)

        for item in self.attachments:
            if item[1].lower().endswith(picture_type):
                self.compress_img = QCheckBox("Compress images", self)
                self.compress_img.setChecked(True)
                self.compress_img.stateChanged.connect(self.on_compress_images_state_changed)
                main.addWidget(self.compress_img)
                break

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.cancel = QPushButton("Cancel")
        self.send = QPushButton("Send")
        self.cancel.setFixedWidth(60)
        self.send.setFixedWidth(60)
        button_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, 
                        QSizePolicy.Policy.Minimum)
        )
        button_layout.addWidget(self.cancel, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self.send, alignment=Qt.AlignmentFlag.AlignRight)

        main.addLayout(button_layout, 1)

        self.setStyleSheet(
            """
            QPushButton{
                padding: 7px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover{
                background-color: #2e2e2e
                }
            QCheckBox{
                font-weight: 600;
                font-size: 13px;
            }
            QCheckBox::indicator{
                border: 1px solid white;
                border-radius: 6px;
                height: 20px;
                width: 20px;
                margin-right: 5px;
            }
            QCheckBox::indicator:checked{
                border-image: url(./public/checked.png) 0 0 0 0 stretch stretch;
            }
            QCheckBox::indicator:unchecked{
                border-image: url(./public/unchecked.png) 0 0 0 0 stretch stretch;
            }
            """
            )

        self.cancel.clicked.connect(self.dialog_reject)
        self.send.clicked.connect(self.dialog_accept)

    def on_compress_images_state_changed(self, state):
        for i in range(len(self.attachments)):
            widget, file, _ = self.attachments[i]
            if not file.lower().endswith(picture_type):
                continue

            if isinstance(widget, QLabel) and state == 0:
                doc = DocAttachment(file, attachment=True)
                self.scroll_layout.replaceWidget(widget, doc)
                widget.deleteLater()
                self.attachments[i] = (doc, file, False)
            elif isinstance(widget, DocAttachment) and state == 2:
                label = self.set_image(file)
                self.scroll_layout.replaceWidget(widget, label)
                widget.deleteLater()
                self.attachments[i] = (label, file, True)
        QApplication.processEvents()
        QTimer.singleShot(1, self.update_geometry)

    def update_geometry(self):
        window_height = self.d_parent.main_window.height()
        contents = self.scroll_contents.children()[1:]
        offset = 97 if hasattr(self, "compress_img") else 65
        content_height = offset
        for w in contents:
            if isinstance(w, QWidget):
                content_height += w.height() + 9
        self.setFixedHeight(min(content_height, window_height * 0.9))
        self.move(self.d_parent.main_window.geometry().center() - self.rect().center())
        

    def dialog_accept(self):
        files: list[tuple[str, bool]] = []
        for item in self.attachments:
            _, file, compressed = item
            files.append((file, compressed))
        self.d_parent.on_dialog_finished(Dialog.DialogCode.Accepted, files)
    
    def dialog_reject(self):
        # Delete temporary file if image was grabbed from the clipboard
        if len(self.data) == 1:
            temp_dir = tempfile.gettempdir()
            file = self.data[0]
            if os.path.commonpath([temp_dir, file]):
                os.remove(file)

        self.d_parent.on_dialog_finished(Dialog.DialogCode.Rejected, [])

    def showEvent(self, event):
        QApplication.processEvents()
        QTimer.singleShot(1, self.update_geometry)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.acceptProposedAction()
        return super().dragEnterEvent(event)

    def set_image(self, path: str) -> QLabel:
        label = QLabel(self)
        label.setScaledContents(True)
        if path[-4:] == ".gif":
            mov = QMovie(path)
            label.setMovie(mov)
            mov.start()
            _pixmap = mov.currentPixmap()
            aspect_ratio = _pixmap.height() / _pixmap.width()
            if aspect_ratio >= 1:
                m = _pixmap.height() / 270
            else:
                m = _pixmap.width() / 300
            label.setFixedSize(int(_pixmap.width()/m), int(_pixmap.height()/m))
        else:
            image = compress_image(image_path=path)
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(
                300, 270, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
        return label
