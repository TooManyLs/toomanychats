import socket
from threading import Thread
from encryption import (
    encrypt_aes, 
    decrypt_aes, 
    generate_sha256, 
    send_encrypted, 
    recv_encrypted
    )
from base64 import b64encode, b64decode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002
SERVER_RSA = RSA.generate(2048)
s_cipher = PKCS1_OAEP.new(SERVER_RSA)
users = {}

f_codes = {
    "admin":\
    "A408DB8643628EAC4C6474814F347EEA06EB51BE8108D3C461EE5DADE74A17ED"}

client_sockets = set()
authenticated_users = {}

def listen_for_client(cs, username):
    while True:
        try:
            msg = cs.recv(4096).decode("utf-8")
            try:
                msg, aes, pub = recv_encrypted(msg)
                if pub == SERVER_RSA.public_key():   
                    dec_key = s_cipher.decrypt(aes)
                    for client in client_sockets:
                        if client != cs:
                            name = ""
                            for user, sock in authenticated_users.items():
                                if sock == client:
                                    name = user
                                    break
                            pubkey = users[name]["public"]
                            client.send(send_encrypted(
                                (msg, dec_key), pubkey
                                ).encode("utf-8"))
                else:
                    cli = ""
                    for user, sub_dict in users.items():
                        if sub_dict['public'] == pub.export_key():
                            cli = authenticated_users[user]
                            cli.send(send_encrypted((msg, aes), pub).encode("utf-8"))
                            break
            except Exception as e:
                handle_command(msg, cs, username)
                continue
        except (OSError, ConnectionResetError):
            print("Socket is closed.")
            if cs in client_sockets:
                client_sockets.remove(cs)
            del authenticated_users[username]
            del f_codes[username]
            cs.close()
            break

def handle_command(cmd, cs, user=None):
    hr = "-" * 80
    if cmd == "!signup":
        try:
            friend_code, friend = cs.recv(1024).decode("utf-8").split("|")
            if f_codes[friend] == friend_code:
                cs.send("approve".encode("utf-8"))
        except (KeyError, ValueError):
            cs.send("reject".encode("utf-8"))
            return  
        reg_info = cs.recv(2048).decode("utf-8")
        reg_info, aes, pub = recv_encrypted(reg_info)
        aes = s_cipher.decrypt(aes)
        reg_info = decrypt_aes(reg_info, aes).decode("utf-8")
        name, passw, salt, pubkey = reg_info.split("|")
        if name not in users:
            cs.send(f"[+] You've successfully created an account!".encode("utf-8"))
            f_codes[friend] = generate_sha256()
            pubkey = pubkey.strip()
            users[name] = {
                "passw": b64decode(passw.encode("utf-8")), 
                "salt": b64decode(salt),
                "public": pubkey.encode("utf-8")
            }
        else:
            cs.send(f"[-] {name} is not available.".encode("utf-8"))
            pass
### Chat commands
    elif cmd == "!userlist":
        user_pub = users[user]["public"]
        userlist =\
         f"[Server]\nUser list:\n{hr}\n{"\n".join(authenticated_users.keys())}\n{hr}"
        cs.send(send_encrypted(encrypt_aes(userlist.encode("utf-8")), user_pub)\
                .encode("utf-8"))
    elif cmd == "!code":
        code = f"[Server]\nYour friend code:\n{hr}\n{f_codes[user]}\n{hr}"
        user_pub = users[user]["public"]
        cs.send(send_encrypted(encrypt_aes(code.encode("utf-8")), user_pub)\
                .encode("utf-8"))

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((SERVER_HOST, SERVER_PORT))
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

while True:
    cli_socket, cli_addr = s.accept()
    print(f"[+] {cli_addr} connected.")
    cli_socket.send(SERVER_RSA.public_key().export_key())
    first_resp = cli_socket.recv(1024).decode("utf-8")
    username = ""
    if first_resp == "!signup":
        handle_command("!signup", cli_socket)
    else:
        username = first_resp
    username = cli_socket.recv(1024).decode("utf-8") if not username else username

    if username in users and username not in authenticated_users:
        password = users[username]["passw"]
        salt = users[username]["salt"]
        user_pub = users[username]["public"]
        challenge, _ = encrypt_aes("OK".encode("utf-8"), password)       
        challenge_string =\
        f"{b64encode(salt).decode("utf-8")}|{b64encode(challenge).decode("utf-8")}"
        cli_socket.send(send_encrypted(
            encrypt_aes(challenge_string.encode("utf-8")), user_pub
            ).encode("utf-8"))

        response = cli_socket.recv(1024).decode("utf-8")
        if response == "OK":
            client_sockets.add(cli_socket)
            authenticated_users[username] = cli_socket
            f_codes[username] = generate_sha256()
            print(f"[+] {username} authenticated successfully.")
            t = Thread(target=listen_for_client, args=(cli_socket, username), daemon=True)
            t.start()
        else:
            print(f"[-] {username} failed to authenticate.")
            cli_socket.close()
    else:
        print(f"[-] No such user as {username}." if username not in users\
               else f"[-] {cli_addr} tries to connect as {username}")
        cli_socket.close()

for cs in list(client_sockets):
    cs.close()
    client_sockets.remove(cs)
s.close()
