from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QHBoxLayout, 
    QWidget, 
    QLabel, 
    QTextEdit, 
    QPushButton, 
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    QFrame
    )
from PySide6.QtGui import QFontMetrics, QPainter, QColor
from PySide6.QtCore import Qt
import datetime


class CustomTextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_text = datetime.datetime.now().strftime("%I:%M %p")

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setPen(QColor('lightgray'))
        rect = self.rect()
        rect.setRight(rect.right() - 15)  # Move 5px to the left
        rect.setBottom(rect.bottom() - 6)  # Move 5px up
        painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, self.time_text)

class ChatBubble(QWidget):
    def __init__(self, text):
        super().__init__()

        self.text_label = CustomTextEdit()
        self.text_label.setStyleSheet(
            """
            border: 1px solid black; 
            padding-left: 5px; 
            border-radius: 10px; 
            background-color: #2e2e2e;
            color: white;
            """
            )
        self.text_label.setReadOnly(True)
        self.text_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.text_label.setText(text)

        layout = QVBoxLayout()
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        self.text_label.setStyleSheet(
            """
            padding-left: 5px; 
            border-radius: 10px; 
            background-color: #2e2e2e;
            color: white;
            """
            )

        metrics = QFontMetrics(self.text_label.font())
        max_width = 500
        text_width = 0
        for i in range(self.text_label.document().blockCount()):
            block = self.text_label.document().findBlockByNumber(i)
            line = block.text()
            width = metrics.horizontalAdvance(line) + 95
            text_width = max(text_width, width)
        self.one_line_height = self.text_label.fontMetrics().lineSpacing()
        lines = (text_width // max_width) + self.text_label.document().blockCount()
        text_height = lines * self.one_line_height + 29
        self.setMinimumSize(min(text_width, max_width), text_height)
        self.setMaximumSize(min(text_width, max_width), text_height)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatroom")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.chat_area = QWidget()
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

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

    def send_message(self):
        message = self.text_input.toPlainText().strip()
        if message:
            bubble = ChatBubble(message)
            self.layout.addWidget(bubble)
            self.text_input.clear()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()