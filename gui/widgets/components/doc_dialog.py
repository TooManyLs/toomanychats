from PySide6.QtWidgets import (
    QDialog, 
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QLabel, 
    QCheckBox, 

    )
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor, 
    QPainter, 
    QPainterPath, 
    QBrush, 
    QPen,
    QPixmap
    )

from .scroll_area import ScrollArea
from .doc_attachment import DocAttachment

picture_type = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")

class Overlay(QWidget):
    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)
        self.setPalette(QColor(0, 0, 0, 120))
        self.setAutoFillBackground(True)

class AttachDialog(QDialog):
    def __init__(self, parent=None, files: list[str]=None):
        super(AttachDialog, self).__init__(parent)
        self.data = files
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(0, 0, 350, 400)

        main = QVBoxLayout(self)
        main.setSpacing(10)

        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_area.setWidget(self.scroll_contents)
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(0,0,0,10)


        self.attachments = []
        for file in self.data:
            if file.endswith(picture_type):
                label = QLabel(self)
                pixmap = QPixmap(file)
                pixmap = pixmap.scaled(
                    300, 270, Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation)
                label.setPixmap(pixmap)
                self.scroll_layout.addWidget(label, alignment=Qt.AlignCenter)
                self.attachments.append((label, file, True))
            else:
                doc = DocAttachment(file, attachment=True)
                self.scroll_layout.addWidget(doc, alignment=Qt.AlignCenter)
                self.attachments.append((doc, file, False))

        main.addWidget(self.scroll_area)

        for i in range(len(self.attachments)):
            if self.attachments[i][1].endswith(picture_type):
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
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(self.cancel, alignment=Qt.AlignRight)
        button_layout.addWidget(self.send, alignment=Qt.AlignRight)

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
            if not file.endswith(picture_type):
                continue

            if isinstance(widget, QLabel) and state == 0:
                doc = DocAttachment(file, attachment=True)
                self.scroll_layout.replaceWidget(widget, doc)
                widget.deleteLater()
                self.attachments[i] = (doc, file, False)
            elif isinstance(widget, DocAttachment) and state == 2:
                label = QLabel(self)
                pixmap = QPixmap(file)
                pixmap = pixmap.scaled(
                    300, 270, Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation)
                label.setPixmap(pixmap)
                self.scroll_layout.replaceWidget(widget, label)
                widget.deleteLater()
                self.attachments[i] = (label, file, True)

    def dialog_accept(self):
        files = []
        for attachment in self.attachments:
            _, file, compressed = attachment
            files.append((file, compressed))
        self.parent().on_dialog_finished(QDialog.Accepted, files)
    
    def dialog_reject(self):
        self.parent().on_dialog_finished(QDialog.Rejected, [])

    def showEvent(self, event):
        try:
            parent_geometry = self.parent().parent().parent().geometry()
        except AttributeError:
            parent_geometry = self.parent().geometry()

        self.move(parent_geometry.center() - self.rect().center())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 12, 12)
        painter.fillPath(path, QBrush(QColor("#1e1e1e")))
        painter.strokePath(path, QPen(Qt.NoPen))