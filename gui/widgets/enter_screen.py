from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QPushButton,
    )

class EnterWidget(QWidget):
    def __init__(self, stacked_layout):
        super().__init__()
        self.stacked_layout = stacked_layout

        layout = QGridLayout()

        self.sign_in_button = QPushButton("Sign In")
        self.sign_up_button = QPushButton("Sign Up")
        buttons = QVBoxLayout()
        buttons.addWidget(self.sign_in_button)
        buttons.addSpacing(20)
        buttons.addWidget(self.sign_up_button)
        
        layout.addItem(buttons, 1, 1)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 2)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.sign_in_button.clicked.connect(self.on_sign_in_clicked)
        self.sign_up_button.clicked.connect(self.on_sign_up_clicked)

    def on_sign_in_clicked(self):
        self.stacked_layout.setCurrentIndex(1)

    def on_sign_up_clicked(self):
        self.stacked_layout.setCurrentIndex(2)