import socket
import random
from threading import Thread
from datetime import datetime
from colorama import Fore, init, Back
from encryption import encrypt, decrypt

init()

colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX,
          Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX,
          Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
          Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.WHITE, Fore.RED,
          Fore.YELLOW,
          ]

cli_color = random.choice(colors)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002
separator_token = "<SEP>"

s = socket.socket()
print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}")
s.connect((SERVER_HOST, SERVER_PORT))
print("[+] Connected.")

name = input("Enter your name: ")
s.send(encrypt(f"{cli_color}{name} connected.\n{Fore.RESET}".encode()))
    
def listen_for_messages():
    while True:
        try:
            msg = s.recv(1024)
            msg = decrypt(msg).decode()
            msg = msg.replace(separator_token, ": ")
            print("\n" + msg)
        except (OSError, ConnectionResetError):
            s.close()
            break
        except Exception:
            break

t = Thread(target=listen_for_messages)
t.daemon = True
t.start()

while True:
    to_send = input()
    if to_send.lower() == "q":
        break
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_send = f"{cli_color}[{now}] {name}{separator_token}{to_send}{Fore.RESET}"
    s.send(encrypt(to_send.encode()))
s.send(encrypt(f"{cli_color}{name} disconnected.{Fore.RESET}".encode()))
s.close()