import socket
import random
from threading import Thread
from datetime import datetime
from colorama import Fore, init, Back
from encryption import encrypt, decrypt, generate_key

init()

colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX,
          Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX,
          Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
          Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.YELLOW,
          ]

cli_color = random.choice(colors)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002
separator_token = "<SEP>"

s = socket.socket()
print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}")
s.connect((SERVER_HOST, SERVER_PORT))
print("[+] Connected.")
name = ""
while not len(name):
    name = input("Enter your username: ")
    if not name or not name.isalnum():
        name = ""
        print("Type valid name.")
password = input("Enter your password: ")
key = generate_key(password, b"chupa")
s.send(name.encode("utf-8"))

challenge = s.recv(1024)
try:
    response = decrypt(challenge, key).decode("utf-8")
    if response == "OK":
        s.send("OK".encode("utf-8"))
        s.send(encrypt(f"{cli_color}{name} connected.{Fore.RESET}".encode()))
        print(f"Welcome, {name}!")
except:
    print("Invalid username or password.")
    s.close()
    exit(1)
    
def listen_for_messages():
    while True:
        try:
            msg = s.recv(1024)
            msg = decrypt(msg).decode("utf-8")
            msg = msg.replace(separator_token, ": ")
            print("\n" + msg)
        except (OSError, ConnectionResetError):
            s.close()
            break
        except Exception:
            break

t = Thread(target=listen_for_messages, daemon=True)
t.start()

while True:
    to_send = input()
    if to_send.lower() == "q":
        break
    if not to_send:
        continue
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_send = f"{cli_color}[{now}] {name}{separator_token}{to_send}{Fore.RESET}"
    print(to_send := to_send.replace(separator_token, ": "))
    s.send(encrypt(to_send.encode("utf-8")))
s.send(encrypt(f"{cli_color}{name} disconnected.{Fore.RESET}".encode("utf-8")))
s.close()