import socket
import random
from threading import Thread
from datetime import datetime
from time import perf_counter
from colorama import Fore, init, Back
from encryption import encrypt, decrypt, generate_key
from base64 import b64decode

init()

colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX,
          Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
          Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
          Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.YELLOW,
          ]
cli_color = random.choice(colors)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002
separator_token = "<SEP>"

def signin():
    name = ""
    while not len(name):
        name = input("Enter your username: ")
        if not name or not name.isalnum():
            name = ""
            print("Type valid name.")
    password = input("Enter your password: ")
    s.send(name.encode("utf-8"))
    try:
        server_resp = decrypt(s.recv(1024)).decode("utf-8")
        salt, challenge = server_resp.split("|")
        key = generate_key(password, salt.encode())

        response = decrypt(b64decode(challenge.encode("utf-8")), key).decode("utf-8")
        if response == "OK":
            s.send("OK".encode("utf-8"))
            s.send(encrypt(f"{cli_color}{name} connected.{Fore.RESET}".encode()))
            print(f"Welcome, {name}!")
            return name
    except:
        print("Invalid username or password.")
        s.close()
        exit(1)

def signup():
    """Should type friend code first to sign up"""
    name = ""
    while len(name) < 3 or not name.isalnum():
        name = input("Enter username: ")
        if len(name) < 3 or not name.isalnum():
            name = ""
            print("Type valid name.")
    password = ""
    while len(password) < 6:
        password = input("Create a password: ")
        if len(password) < 6:
            password = ""
            print("Password is too short.")
    print(f"{Fore.LIGHTGREEN_EX}You've succesfully created an account!{Fore.RESET}")
    signin()

def listen_for_messages():
    while True:
        try:
            msg = decrypt(s.recv(1024)).decode("utf-8")
            msg = msg.replace(separator_token, ": ", 1)
            if msg[:8] == "[Server]":
                print(f"\n{Fore.LIGHTGREEN_EX}{msg}{Fore.RESET}")
            else:
                print("\n" + msg)
        except (OSError, ConnectionResetError):
            break

s = socket.socket()
print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}")
s.connect((SERVER_HOST, SERVER_PORT))
print("[+] Connected.")
enter = input("!s to sign in | !r to sign up: ")
if enter == "!s":
    name = signin()
elif enter == "!r":
    name = signup()
else:
    s.close()
    exit(1)

    

t = Thread(target=listen_for_messages, daemon=True)
t.start()

cmd_t_o = [0]

while True:
    to_send = input()
    if to_send.lower() == "q":
        break
    if not to_send:
        continue
    if to_send == "!userlist":
        t_o = perf_counter()
        if abs(t_o - cmd_t_o[0]) < 3:
            print(f"\n{Back.RED}{Fore.BLACK}[!] Command timeout 3s.{Fore.RESET}{Back.RESET}")
        else:
            s.send(to_send.encode("utf-8"))
        cmd_t_o[0] = t_o
        continue
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_send = f"{cli_color}[{now}] {name}{separator_token}{to_send}{Fore.RESET}"
    print(t := to_send.replace(separator_token, ": ", 1))
    s.send(encrypt(to_send.encode("utf-8")))
s.send(encrypt(f"{cli_color}{name} disconnected.{Fore.RESET}".encode("utf-8")))
s.close()