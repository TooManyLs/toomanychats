from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QPushButton,
    )

class EnterWidget(QWidget):
    def __init__(self, stacked_layout, s):
        super().__init__()
        self.stacked_layout = stacked_layout
        self.s = s

        layout = QGridLayout()

        self.sign_in_button = QPushButton("Sign In")
        self.sign_up_button = QPushButton("Sign Up")
        self.sign_up_button.setObjectName("reg")
        buttons = QVBoxLayout()
        buttons.addWidget(self.sign_in_button)
        buttons.addSpacing(20)
        buttons.addWidget(self.sign_up_button)
        
        layout.addItem(buttons, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.setStyleSheet(
            """
            QPushButton{
                background-color: #2e2e2e;
                height: 45px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                outline: none;
            }
            QPushButton:hover{
                background-color: #3e3e3e;
            }
            QPushButton:pressed{background-color: #5e5e5e;}
            #reg{
                background-color: #1e1e1e;
                border: 2px solid #2e2e2e;
            }
            #reg:hover{
                background-color: #3e3e3e;
                border: none;
                color: #1e1e1e;
            }
            #reg:pressed{background-color: #5e5e5e;}
            """
            )

        self.sign_in_button.clicked.connect(self.on_sign_in_clicked)
        self.sign_up_button.clicked.connect(self.on_sign_up_clicked)

    def on_sign_in_clicked(self):
        self.stacked_layout.setCurrentIndex(1)

    def on_sign_up_clicked(self):
        self.s.send("/signup".encode())
        self.stacked_layout.setCurrentIndex(2)