from PySide6.QtWidgets import (
    QLineEdit, 
    QLabel, 
    QGraphicsDropShadowEffect, 
    QSizePolicy, 
    QTextEdit, 
    QPushButton, 
    QHBoxLayout,
    )
from PySide6.QtGui import QPainter, QTextDocumentFragment, QIcon, QTextDocument
from PySide6.QtCore import Qt, QSize

class TextField(QLineEdit):
    def __init__(self, label: str=None, drop_shadow=False, show_hide=None, parent=None):
        super(TextField, self).__init__(parent)
        self.label = QLabel(label)
        self.label.hide()
        self.label.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 0);
            letter-spacing: 2px;
            font-weight: 600;
            """)
        self.setFrame(False)
        super(TextField, self).setStyleSheet("background-color: #2e2e2e;")
        if drop_shadow is not None:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(0)
            shadow.setColor(drop_shadow)
            self.setGraphicsEffect(shadow)

        if show_hide:
            self.setEchoMode(QLineEdit.Password)
            self.setStyleSheet(
                """
                padding-right: 45px; 
                background-color: #2e2e2e;
                """
                )
            self.button = QPushButton("")
            self.button.setIcon(QIcon("./public/show.png"))
            self.button.setIconSize(QSize(18, 18))
            self.button.setCursor(Qt.ArrowCursor)
            self.button.setStyleSheet(
                """QPushButton{
                        border: none; 
                        padding: 0px;
                        border-radius: 6px;
                        height: 28px;
                        width: 28px;
                    }
                """
                )
            self.button.clicked.connect(self.toggle_visibility)
            layout = QHBoxLayout(self)
            layout.addWidget(self.button, alignment=Qt.AlignRight)

    def paintEvent(self, event):
        super(TextField, self).paintEvent(event)
        painter = QPainter(self)
        painter.drawPixmap(7, 3, self.label.grab())
    
    def toggle_visibility(self):
        if self.echoMode() == QLineEdit.Normal:
            self.setEchoMode(QLineEdit.Password)
            self.button.setIcon(QIcon("./public/show.png"))
        else:
            self.setEchoMode(QLineEdit.Normal)
            self.button.setIcon(QIcon("./public/hide.png"))

class TextArea(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.one_line_height = self.fontMetrics().lineSpacing()
        self.setMaximumHeight(self.one_line_height * 12 + 12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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
        text = source.text()
        fragment = QTextDocumentFragment.fromPlainText(text)
        self.textCursor().insertFragment(fragment)