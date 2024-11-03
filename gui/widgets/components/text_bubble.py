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
from .textarea import TextArea

class TextBubble(QTextEdit):
    def __init__(
            self, parent: QWidget, text, name=None,
            timestamp:datetime | None = None, *args,
            unknown: bool = False, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.unknown = unknown
        self.p = parent
        self.setPlainText(text)
        self.setReadOnly(True)
        self.name = name
        self.time_text = (timestamp if timestamp
                          else datetime.now()).strftime("%I:%M %p")
        self.metrics = QFontMetrics(self.font())
        self.padding = " " * 20 + "\u200B"
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        style = """
            padding-left: 5px; 
            padding-right: 5px; 
            border-radius: 12px; 
            background-color: #2e2e2e;
            """
        self.setStyleSheet(
                style
            )
        if name:
            self.setViewportMargins(0, 14, 0, 0)
            self.name = QPushButton(name)
            self.name.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.name.clicked.connect(lambda: print(f"pushed {name}"))
            self.name.setSizePolicy(
                    QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
                    )
            self.name.setMaximumWidth(
                self.metrics.horizontalAdvance(self.name.text()) + 10
                )
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
                """
                )
            layout.addWidget(self.name, alignment=Qt.AlignmentFlag.AlignTop) 
        
        if self.unknown:
            font = self.font()
            font.setItalic(True)
            self.setFont(font)
            self.setStyleSheet(style + " color: gray;")
            self.setText("This message cannot be displayed.\nUpdate your app to see the content of this message.")

        self.counter = 0 
        self.sel: TextArea
        self.chat: QWidget
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
        parent_width = self.p.size().width()
        lines = text.split('\n')
        text_width = max(
            (max(
                self.metrics.horizontalAdvance(line) for line in lines) + 85),
                (self.metrics.horizontalAdvance(self.name.text()) 
                 * 1.185 if self.name else 0)
            )
        if text_width > parent_width * 0.8:
            text_width = parent_width * 0.8

        self.setFixedWidth(min(int(text_width), 500))

        doc = QTextDocument(self.toPlainText() + self.padding)
        doc.setDefaultFont(self.font())
        doc.setTextWidth(self.width())
        doc.setDocumentMargin(9.0)
        text_height = doc.size().height() - 6
        if self.name:
            text_height += 13
        self.setFixedHeight(int(text_height))

    def focusInEvent(self, e) -> None:
        for o in self.chat.children():
            if isinstance(o, TextBubble) and o != self:
                cursor = o.textCursor()
                cursor.clearSelection()
                o.setTextCursor(cursor) 
        super().focusInEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)

        painter = QPainter(self.viewport())
        painter.setPen(QColor('gray'))
        rect = self.rect()
        rect.setRight(rect.right() - 12)
        if self.name:
            rect.setBottom(rect.bottom() - 17)
        else:
            rect.setBottom(rect.bottom() - 3)
        painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                self.time_text
                )

    def contextMenuEvent(self, e) -> None:
        if self.unknown:
            return

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
        self.menu.exec(e.globalPos())

    def copy_text(self, copy_all=True):
        if copy_all:
            self.selectAll()
        self.copy()
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
