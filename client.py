import socket
import random
import os
from threading import Thread
from datetime import datetime
from time import perf_counter
from colorama import Fore, init, Back
from encryption import (
    encrypt_aes, 
    decrypt_aes, 
    generate_key, 
    send_encrypted,
    recv_encrypted
    )
from base64 import b64decode, b64encode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

init()

colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX,
          Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
          Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX,
          Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.YELLOW,
          ]
cli_color = random.choice(colors)

address = input("Enter the address of the server: ").split(":")
SERVER_HOST = address[0]
SERVER_PORT = int(address[1])
separator_token = "<SEP>"

def signin():
    name = ""
    while not len(name):
        name = input("Enter your username: ")
        if not name or not name.isalnum():
            name = ""
            print("Type valid name.")
    password = input("Enter your password: ")
    s.send(name.encode('utf-8'))
    try:
        with open(f"keys/{name}_private.pem", "rb") as f:
            my_pvtkey = RSA.import_key(f.read())
        my_cipher = PKCS1_OAEP.new(my_pvtkey)
        data = s.recv(2048).decode('utf-8')
        data, aes, pub = recv_encrypted(data)
        aes = my_cipher.decrypt(aes)
        server_resp = decrypt_aes(data, aes).decode('utf-8')
        salt, challenge = server_resp.split("|")
        key = generate_key(password, b64decode(salt.encode('utf-8')))
        response = decrypt_aes(b64decode(challenge.encode('utf-8')), key).decode('utf-8')
        if response == "OK":
            s.send("OK".encode('utf-8'))
            connected = encrypt_aes(f"{cli_color}{name} connected.{Fore.RESET}"\
                                    .encode('utf-8'))
            s.send(send_encrypted(connected, server_pubkey).encode('utf-8'))
            print(f"Welcome, {name}!")
            return name, my_cipher
    except Exception:
        print("Invalid username or password.")
        s.close()
        exit(1)

def signup():
    s.send("/signup".encode('utf-8'))
    friend_code = input("Enter friend code and his nickname splitted with '|' to countinue registration: ")
    s.send(friend_code.encode('utf-8'))
    resp = s.recv(1024).decode('utf-8')
    if resp == "reject":
        print("No such code.")
        s.close()
        exit(1)
    name = ""
    while len(name) < 3 or not name.isalnum():
        name = input("Enter username: ")
        if len(name) < 3 or not name.isalnum() or len(name) > 20:
            name = ""
            print("Type valid name. (3-20 alphanumeric chars)")
    password = ""
    while len(password) < 8:
        password = input("Create a password (minimum 8 symbols): ")
        if len(password) < 8:
            password = ""
            print("Password is too short.")
    salt = os.urandom(16)
    hash = generate_key(password, salt)
    rsa_keys = RSA.generate(2048)
    pubkey = rsa_keys.public_key().export_key()
    pvtkey = rsa_keys.export_key()
    data = encrypt_aes(f"{name}|{b64encode(hash).decode('utf-8')}|\
{b64encode(salt).decode('utf-8')}|\
{pubkey.decode('utf-8')}".encode('utf-8'))
    s.send(send_encrypted(data, server_pubkey).encode('utf-8'))
    ok = s.recv(1024).decode('utf-8')
    if "[+]" in ok:
        with open(f"keys/{name}_private.pem", "wb") as f:
            f.write(pvtkey)
    print(ok)
    return signin()

def listen_for_messages():
    while True:
        try:
            data = s.recv(10000).decode('utf-8')
            data, aes, pub = recv_encrypted(data)
            aes = my_cipher.decrypt(aes)
            msg = decrypt_aes(data, aes).decode('utf-8')
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
server_pubkey = RSA.import_key(s.recv(1024))
print("[+] Connected.")
enter = input("/s to sign in | /r to sign up: ")
if enter == "/s":
    name, my_cipher = signin()
elif enter == "/r":
    name, my_cipher = signup()
else:
    s.close()
    exit(1)

t = Thread(target=listen_for_messages, daemon=True)
t.start()

cmd_t_o = [0]
timeout_warn = f"\n{Back.RED}{Fore.BLACK}[!] Command timeout 3s.{Fore.RESET}{Back.RESET}"
while True:
    to_send = input()
    if to_send.lower() == "q":
        break
    if not to_send:
        continue
### Chat commands
    if to_send == "/userlist":
        t_o = perf_counter()
        if abs(t_o - cmd_t_o[0]) < 3:
            print(timeout_warn)
        else:
            s.send(to_send.encode('utf-8'))
        cmd_t_o[0] = t_o
        continue
    if to_send == "/code":
        t_o = perf_counter()
        if abs(t_o - cmd_t_o[0]) < 3:
            print(timeout_warn)
        else:
            s.send(to_send.encode('utf-8'))
        cmd_t_o[0] = t_o
        continue
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_send = f"{cli_color}[{now}] {name}{separator_token}{to_send}{Fore.RESET}"
    print(t := to_send.replace(separator_token, ": ", 1))
    to_send = encrypt_aes(to_send.encode('utf-8'))
    s.send(send_encrypted(to_send, server_pubkey).encode('utf-8'))
dc = encrypt_aes(f"{cli_color}{name} disconnected.{Fore.RESET}".encode('utf-8'))
s.send(send_encrypted(dc, server_pubkey).encode('utf-8'))
s.close()