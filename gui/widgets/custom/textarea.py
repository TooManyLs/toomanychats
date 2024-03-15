from PySide6.QtWidgets import QSizePolicy, QTextEdit
from PySide6.QtGui import QTextDocumentFragment, QTextDocument
from PySide6.QtCore import Qt

class TextArea(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.one_line_height = self.fontMetrics().lineSpacing()
        self.setMaximumHeight(self.one_line_height * 12 + 12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

    def compute_height(self):
        doc = QTextDocument(self.toPlainText())
        doc.setDefaultFont(self.font())
        doc.setTextWidth(self.width())
        text_height = doc.size().height() + 4

        if text_height <= self.maximumHeight():
            self.setMinimumHeight(text_height)
        else:
            self.setMinimumHeight(self.maximumHeight())

    def paintEvent(self, event):
        self.compute_height()
        return super().paintEvent(event)
    
    def insertFromMimeData(self, source):
        if source.hasUrls():
            files = [u.toLocalFile() for u in source.urls()]
            try:
                self.parent().attach_file(files)
            except AttributeError:
                self.parent().parent().attach_file(files)
            return
        text = source.text()
        fragment = QTextDocumentFragment.fromPlainText(text)
        self.textCursor().insertFragment(fragment)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            try:
                self.parent().on_send()
            except AttributeError:
                self.parent().parent().on_send()
        else:
            super().keyPressEvent(event)