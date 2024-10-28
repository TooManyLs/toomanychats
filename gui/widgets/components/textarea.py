import os
import tempfile

from PySide6.QtWidgets import QSizePolicy, QTextEdit
from PySide6.QtGui import QTextDocumentFragment, QTextDocument
from PySide6.QtCore import Qt, QPoint, Signal

from . import CustomMenu
from ..utils.tools import qimage_to_bytes

class TextArea(QTextEdit):
    attach = Signal(list)
    send = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.one_line_height = self.fontMetrics().lineSpacing()
        self.setMaximumHeight(self.one_line_height * 12 + 12)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background-color: #161616; color: white;")

    def compute_height(self):
        doc = QTextDocument(self.toPlainText())
        doc.setDefaultFont(self.font())
        doc.setTextWidth(self.width())
        text_height = doc.size().height() + 4

        if text_height <= self.maximumHeight():
            self.setMinimumHeight(int(text_height))
        else:
            self.setMinimumHeight(self.maximumHeight())

    def paintEvent(self, e):
        self.compute_height()
        return super().paintEvent(e)
    
    def insertFromMimeData(self, source):
        if source.hasImage():
            with tempfile.NamedTemporaryFile(
                "w+b", suffix=".jpg", delete=False,
                delete_on_close=False
            ) as tmp:
                tmp.write(qimage_to_bytes(source.imageData()))
                self.attach.emit([tmp.name])
            return
        if source.hasUrls():
            for url in source.urls():
                if os.path.isdir(url.toLocalFile()):
                    return
            files = [u.toLocalFile() for u in source.urls()]
            self.attach.emit(files)
            return
        text = source.text()
        fragment = QTextDocumentFragment.fromPlainText(text)
        self.textCursor().insertFragment(fragment)

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key.Key_Return and not e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.send.emit()
        else:
            super().keyPressEvent(e)

    def dragEnterEvent(self, e) -> None:
        if e.mimeData().hasUrls():
            e.ignore()
            return
        return super().dragEnterEvent(e)
    
    def contextMenuEvent(self, e) -> None:
        selection = self.textCursor().hasSelection()
        can_undo = self.document().isUndoAvailable()
        can_redo = self.document().isRedoAvailable()

        self.menu = CustomMenu(self)
        self.menu.add_action("Undo", self.undo, shortcut="Ctrl+Z",
                             status=can_undo)
        self.menu.add_action("Redo", self.redo, shortcut="Ctrl+Y",
                             status=can_redo)
        self.menu.add_separator()
        self.menu.add_action("Cut", self.cut, shortcut="Ctrl+X", 
                             status=selection)
        self.menu.add_action("Copy", self.copy, shortcut="Ctrl+C",
                             status=selection)
        self.menu.add_action("Paste", self.paste, shortcut="Ctrl+V",
                             status=self.canPaste())
        self.menu.add_action("Delete", self.textCursor().deleteChar,
                             status=selection)
        self.menu.add_separator()
        self.menu.add_action("Select all", self.selectAll, shortcut="Ctrl+A",
                             status=bool(self.toPlainText()))
        self.menu.exec(e.globalPos() + QPoint(0, -self.menu.h))
