from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, 
    QTextEdit, 
    QPushButton, 
    QSizePolicy,
    QWidget
    )
from PySide6.QtGui import (
    QFontMetrics, 
    QPainter, 
    QColor,
    QResizeEvent, 
    QTextDocument, 
    QCursor,
    )
from PySide6.QtCore import Qt

from .custom_menu import CustomMenu
from ..custom import TextArea

class TextBubble(QTextEdit):
    def __init__(self, text, name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlainText(text)
        self.setReadOnly(True)
        self.name = name
        self.time_text = datetime.now().strftime("%I:%M %p")
        self.metrics = QFontMetrics(self.font())
        self.padding = " " * 20 + "\u200B"
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(
            """
            padding-left: 5px; 
            padding-right: 5px; 
            border-radius: 12px; 
            background-color: #2e2e2e;
            color: white;
            """
            )
        if name:
            self.setViewportMargins(0, 14, 0, 0)
            self.name = QPushButton(name)
            self.name.setCursor(QCursor(Qt.PointingHandCursor))
            self.name.clicked.connect(lambda: print(f"pushed {name}"))
            self.name.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.name.setMaximumWidth(
                self.metrics.horizontalAdvance(self.name.text()) * 1.3)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0,0,0,0)
            layout.setSpacing(0)
            self.name.setStyleSheet(
                """
                    background-color: rgba(0,0,0,0); 
                    padding-top: 2px; 
                    padding-left: 1px;
                    padding-bottom: 0px;
                    font-weight: 700;
                    border: none;
                    text-align: left;
                    outline: none;
                """
                )
            layout.addWidget(self.name, alignment=Qt.AlignTop) 
        self.counter = 0 
        self.sel: TextArea = None
        self.chat: QWidget = None
        self.selectionChanged.connect(self.selection_changed)

    def selection_changed(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.setFocus()
        else:
            self.sel.setFocus()

    def resizeEvent(self, e: QResizeEvent) -> None:
        while self.counter < 1:
            self.compute_size()
            self.counter = 1
        return super().resizeEvent(e)

    def compute_size(self):
        text = self.toPlainText()
        parent_width = self.parent().parent().parent().size().width()
        lines = text.split('\n')
        text_width = max(
            (max(
                self.metrics.horizontalAdvance(line) for line in lines) + 85),
                (self.metrics.horizontalAdvance(self.name.text()) 
                 * 1.185 if self.name else 0)
            )
        if text_width > parent_width * 0.8:
            text_width = parent_width * 0.8

        self.setFixedWidth(min(text_width, 500))

        doc = QTextDocument(self.toPlainText() + self.padding)
        doc.setDefaultFont(self.font())
        doc.setTextWidth(self.width())
        doc.setDocumentMargin(9.0)
        text_height = doc.size().height() - 6
        if self.name:
            text_height += 13
        self.setFixedHeight(text_height)

    def focusInEvent(self, event) -> None:
        for o in self.chat.children():
            if isinstance(o, TextBubble) and o != self:
                cursor = o.textCursor()
                cursor.clearSelection()
                o.setTextCursor(cursor) 
        super().focusInEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setPen(QColor('gray'))
        rect = self.rect()
        rect.setRight(rect.right() - 12)
        if self.name:
            rect.setBottom(rect.bottom() - 17)
        else:
            rect.setBottom(rect.bottom() - 3)
        painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, self.time_text)

    def contextMenuEvent(self, ev) -> None:
        self.menu = CustomMenu(self)
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.menu.add_action("Copy selected text", 
                                 lambda:self.copy_text(False), 
                                 shortcut="Ctrl+C")
        else:
            self.menu.add_action("Copy text", lambda:self.copy_text(True))
        self.menu.add_action("Delete", lambda:self.deleteLater(), 
                             style="color: #e03e3e")
        self.menu.exec(ev.globalPos())

    def copy_text(self, copy_all=True):
        if copy_all:
            self.selectAll()
        self.copy()
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor) 
        self.menu.close()