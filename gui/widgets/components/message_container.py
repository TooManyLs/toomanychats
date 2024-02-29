from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout,  
    QWidget, 
    QTextEdit, 
    QPushButton, 
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    )
from PySide6.QtGui import (
    QFontMetrics, 
    QTextLayout, 
    QPainter, 
    QColor, 
    QTextOption, 
    QTextDocument,
    )
from PySide6.QtCore import Qt
import datetime

class CustomTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_text = datetime.datetime.now().strftime("%I:%M %p")
        self.metrics = QFontMetrics(self.font())
        self.padding = " " * 28 + "\u200B"
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def focusOutEvent(self, event):       
        text_cursor = self.textCursor()
        text_cursor.clearSelection()
        self.setTextCursor(text_cursor)

        super().focusOutEvent(event)

    def paintEvent(self, event):
        text = self.toPlainText()
        parent_width = self.parent().parent().parent().size().width()
        lines = text.split('\n')
        text_width = max(self.metrics.horizontalAdvance(line) for line in lines) + 85
        if text_width > parent_width * 0.8:
            text_width = parent_width * 0.8

        self.setFixedWidth(min(text_width, 500))

        hor_adv = self.metrics.horizontalAdvance(text)

        if ((hor_adv >= self.width()
        or (hor_adv + 80 >= self.width()
        and self.height() == 27.0))
        and not self.padding in text):
            self.setText(text + self.padding)
        elif (hor_adv < self.width()
        and self.padding in text):
            self.setText(text[:-29])

        doc = QTextDocument(self.toPlainText())
        doc.setDefaultFont(self.font())
        doc.setTextWidth(self.width())
        text_height = doc.size().height() + 3

        self.setFixedHeight(text_height)

        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setPen(QColor('lightgray'))
        rect = self.rect()
        rect.setRight(rect.right() - 15)
        rect.setBottom(rect.bottom() - 6)
        painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, self.time_text)

class ChatBubble(QWidget):
    def __init__(self, text):
        super().__init__()

        self.text_label = CustomTextEdit()
        self.text_label.setText(text)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        self.setStyleSheet(
            """
            padding-left: 5px; 
            padding-right: 5px; 
            border-radius: 12px; 
            background-color: #2e2e2e;
            color: white;
            """
            )
    def paintEvent(self, event):
        h = self.text_label.size().height()
        w = self.text_label.size().width()
        self.setMaximumSize(w + 5, h)
        return super().paintEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatroom")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.chat_area = QWidget()
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.setSpacing(5)
        self.layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.text_input = QTextEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.text_input)
        main_layout.addWidget(self.send_button)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setMinimumWidth(400)

    def send_message(self):
        message = self.text_input.toPlainText().strip()
        if message:
            bubble = ChatBubble(message)
            self.layout.addWidget(bubble, alignment=Qt.AlignRight)
            self.text_input.clear()
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()