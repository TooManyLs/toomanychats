import sys
import atexit
import socket
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QStackedLayout,
    )
from Crypto.PublicKey import RSA

from widgets.enter_screen import EnterWidget
from widgets.signin_screen import SignIn
from widgets.signup_screen import SignUp
from widgets.chat_screen import ChatWidget

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.s = socket.socket()
        print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}")
        self.s.connect((SERVER_HOST, SERVER_PORT))
        self.server_pubkey = RSA.import_key(self.s.recv(1024))
        # self.server_pubkey = ""
        print("[+] Connected.")

        self.setWindowTitle("TooManyChats")

        self.stacked_layout = QStackedLayout()

        # Screens' initialization
        self.enter_widget = EnterWidget(self.stacked_layout)
        self.sign_in = SignIn(self.stacked_layout, self.s, self.server_pubkey)
        self.sign_up = SignUp(self.stacked_layout, self.s, self.server_pubkey)
        self.main_widget = ChatWidget(self.stacked_layout, self.s, self.server_pubkey)

        self.sign_in.name_signal.connect(self.main_widget.listen_for_messages)

        self.stacked_layout.addWidget(self.enter_widget)    # 0
        self.stacked_layout.addWidget(self.sign_in)         # 1
        self.stacked_layout.addWidget(self.sign_up)         # 2
        self.stacked_layout.addWidget(self.main_widget)     # 3

        container = QWidget()
        container.setLayout(self.stacked_layout)

        self.setCentralWidget(container)

        atexit.register(self.quit)
        self.setMinimumWidth(400)

    def quit(self):
        self.s.close()

app = QApplication(sys.argv)
app.setStyle("Fusion")

window = MainWindow()
window.resize(1000, 800)
window.show()

app.exec()