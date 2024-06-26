import os

from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout,  
    QHBoxLayout,  
    QWidget, 
    QPushButton, 
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
    QDialog,
    )
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QCursor

from widgets.components import (TextBubble, SingleImage, ScrollArea, 
                                DocAttachment, AttachDialog, Overlay,
                                TextArea, ChatHeader)
from widgets.utils.tools import compress_image

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Chatroom")
        self.overlay = Overlay(self)
        self.overlay.hide()

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.horizontalScrollBar().setEnabled(False)

        self.chat_area = QWidget()
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.setSpacing(5)
        self.layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
        attach_icon = QIcon("./public/attach.png")
        self.attach = QPushButton(icon=attach_icon)
        self.text_input = TextArea()
        self.send_button = QPushButton("Send")
        self.attach.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.text_input.setPlaceholderText("Write a message...")
        self.text_input.setObjectName("tarea")
        self.send_button.clicked.connect(self.on_send)
        self.attach.clicked.connect(self.attach_file)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(7,7,7,7)
        input_layout.addWidget(self.attach)
        input_layout.addWidget(self.text_input)
        input_layout.addWidget(self.send_button)

        self.header = ChatHeader()
        self.header.reinit.connect(self.initUI)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.header)
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(input_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setMinimumWidth(400)
        self.setMinimumHeight(600)
        self.setStyleSheet("QPushButton{border: none;}")

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.overlay.setParent(main_widget)
        self.overlay.resize(main_widget.size())

        dft = TextBubble("DEFAULT TEXT", "Bryan")
        dft2 = TextBubble("TEST TEXT", "Hannah")
        dft3 = TextBubble(
            """The silver swan, who living had no note,
When death approached, unlocked her silent throat;
Leaning her breast against the reedy shore,
Thus sung her first and last, and sung no more:
Farewell, all joys; 
Oh death, come close mine eyes;
More geese than swans now live, more fools than wise.""", 
        )
        compressed = compress_image("E:/Dloads/monke1.jpg")
        img = SingleImage(compressed)
        img2 = SingleImage()
        doc = DocAttachment("E:/Dloads/3621c770122a7ff74f78cd1ff9ea0bc0.jpg")
        self.layout.addWidget(img, alignment=Qt.AlignRight)
        self.layout.addWidget(img2, alignment=Qt.AlignRight)
        self.layout.addWidget(dft, alignment=Qt.AlignLeft)
        self.layout.addWidget(dft3, alignment=Qt.AlignRight)
        self.layout.addWidget(dft2, alignment=Qt.AlignLeft)
        self.layout.addWidget(doc, alignment=Qt.AlignLeft)

        self.setStyleSheet(
            """
            QPushButton{
                border-radius: 6px;
                padding: 7px;
            }
            QPushButton:hover{
                background-color: #2e2e2e;
            }
            #tarea{
                border: none;
                background-color: #1e1e1e;
            }
            """
            )
        self.scroll_area.setFocusProxy(self.text_input)
        self.attach.setFocusProxy(self.text_input)
        self.send_button.setFocusProxy(self.text_input)
        for o in self.chat_area.children():
            if isinstance(o, QWidget) and not isinstance(o, TextBubble):
                o.setFocusProxy(self.text_input)
            elif isinstance(o, TextBubble):
                o.sel = self.text_input
                o.chat = self.chat_area

    def attach_file(self, files=None):
        if not files:
            files, _ = QFileDialog().getOpenFileNames(
                self, "Choose Files", 
                filter="All files (*.*)")
        if files:
            self.dialog = AttachDialog(self, files=files)
            self.overlay.show()
            self.dialog.show()

    def on_dialog_finished(self, result, files):
        self.dialog.hide()
        self.overlay.hide()
        if result == QDialog.Accepted:
            self.display_attach(files)
    
    def moveEvent(self, event):
        if hasattr(self, 'dialog'):
            parent_geometry = self.geometry()
            self.dialog.move(parent_geometry.center() - self.dialog.rect().center())

    def scroll_down(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.scroll_area.old_max = scrollbar.maximum()
        self.scroll_area.relative_position = (
            scrollbar.value() / self.scroll_area.old_max
            if self.scroll_area.old_max > 0 else 0)

    def on_send(self):
        message = self.text_input.toPlainText().strip()
        if message:
            bubble = TextBubble(message)
            bubble.setFocusProxy(self.text_input)
            self.layout.addWidget(bubble, alignment=Qt.AlignRight)
        self.text_input.clear()
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def display_attach(self, files):
        for f, compressed in files:
            if compressed:
                img = SingleImage(compress_image(f))
                img.setFocusProxy(self.text_input)
                self.layout.addWidget(img, alignment=Qt.AlignRight)
            else:
                doc = DocAttachment(f)
                doc.setFocusProxy(self.text_input)
                self.layout.addWidget(doc, alignment=Qt.AlignRight)
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def resizeEvent(self, event):
        # Keeps dialog in the center of the window
        self.overlay.resize(event.size())
        if hasattr(self, 'dialog'):
            self.dialog.update_geometry()
            event.accept()
        # Resizes all widgets contained in scroll area
        for c in self.chat_area.children():
            if c.isWidgetType():
                try:
                    c.compute_size()
                except AttributeError:
                    c.name_text.compute_size()
    
    def showEvent(self, event):
        self.overlay.resize(self.window().size())
        event.accept()

    def dragEnterEvent(self, event):
        try:
            if event.source().window() is self:
                return
        except AttributeError:
            pass
        try:
            if self.dialog.isVisible():
                return
        except AttributeError:
            pass
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if os.path.isdir(url.toLocalFile()):
                    event.ignore() 
                    return            
            event.acceptProposedAction()
            self.overlay.show()
        else:
            event.ignore()
        
    def dragLeaveEvent(self, event):
        self.overlay.hide()
        return super().dragLeaveEvent(event)
    
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.attach_file(files)

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    window.resize(400, 800)
    window.show()
    app.exec()