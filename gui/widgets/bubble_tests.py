from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout,  
    QHBoxLayout, 
    QWidget, 
    QPushButton, 
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    )
from PySide6.QtCore import Qt

from components import TextBubble
from custom import TextArea

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatroom")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().rangeChanged.connect(
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        )

        self.chat_area = QWidget()
        self.scroll_area.setWidget(self.chat_area)

        self.layout = QVBoxLayout(self.chat_area)
        self.layout.setSpacing(5)
        self.layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.text_input = TextArea()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.text_input)
        input_layout.addWidget(self.send_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(input_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setMinimumWidth(400)

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
        self.layout.addWidget(dft, alignment=Qt.AlignLeft)
        self.layout.addWidget(dft3, alignment=Qt.AlignRight)
        self.layout.addWidget(dft2, alignment=Qt.AlignLeft)

    def send_message(self):
        message = self.text_input.toPlainText().strip()
        if message:
            bubble = TextBubble(message)
            self.layout.addWidget(bubble, alignment=Qt.AlignRight)
        self.text_input.clear()

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    app.exec()