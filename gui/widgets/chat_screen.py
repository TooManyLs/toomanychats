from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    )
from datetime import datetime

from widgets.custom.textfield import TextArea

class ChatWidget(QWidget):
    def __init__(self, stacked_layout, s, server_pubkey):
        super().__init__()
        self.stacked_layout = stacked_layout

        layout = QVBoxLayout()

        self.label = QLabel()
        self.button = QPushButton("Send")
        self.send_field = TextArea()
        self.send_field.setPlaceholderText("Write a message...")
        self.send_field.setObjectName("tarea")
        self.setStyleSheet(
            """
            #tarea{
                border: none;
            }
            """
            )

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)

        layout.addWidget(self.label)
        layout.addLayout(input_layout)

        self.setLayout(layout)

        self.button.clicked.connect(self.on_send)

    def on_send(self):
        now = datetime.now()
        date = now.strftime("%m/%d/%Y")
        time = now.strftime("%I:%M %p")

        to_send = self.send_field.text()
        if to_send:
            print(date, "at", time, to_send)

            self.send_field.clear()