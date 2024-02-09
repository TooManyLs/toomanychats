import socket
from threading import Thread
from encryption import encrypt, decrypt, generate_sha256
from base64 import b64encode, b64decode

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002

users = {}

f_codes = {
    "admin":\
          "A408DB8643628EAC4C6474814F347EEA06EB51BE8108D3C461EE5DADE74A17ED"} 
#server-admin-friend_code

client_sockets = set()
authenticated_users = []

def listen_for_client(cs, username):
    while True:
        try:
            msg = cs.recv(1024)
            try:
                if msg.decode("utf-8"):
                    handle_command(msg, cs, username)
                    continue
            except:
                pass
            for client in client_sockets:
                if client != cs:
                    client.send(msg)
        except (OSError, ConnectionResetError):
            print("Socket is closed.")
            if cs in client_sockets:
                client_sockets.remove(cs)
            authenticated_users.remove(username)
            del f_codes[username]
            cs.close()
            break

def handle_command(cmd, cs, user=None):
    hr = "-" * 80
    if cmd.decode("utf-8") == "!signup":
        try:
            friend_code, friend = cs.recv(1024).decode("utf-8").split("|")
            if f_codes[friend] == friend_code:
                cs.send("approve".encode("utf-8"))
        except (KeyError, ValueError):
            cs.send("reject".encode("utf-8"))
            return  
        reg_info = cs.recv(1024)
        reg_info = decrypt(reg_info).decode("utf-8")
        name, passw, salt = reg_info.split("|")
        if name not in users:
            cs.send(f"[+] You've successfully created an account!".encode("utf-8"))
            f_codes[friend] = generate_sha256()
            users[name] = {"passw": b64decode(passw.encode("utf-8")), "salt": b64decode(salt)}
        else:
            cs.send(f"[-] {name} is not available.".encode("utf-8"))
            pass
### Chat commands
    elif cmd.decode("utf-8") == "!userlist":
        userlist = f"[Server]\nUser list:\n{hr}\n{"\n".join(authenticated_users)}\n{hr}"
        cs.send(encrypt(userlist.encode("utf-8")))
    elif cmd.decode("utf-8") == "!code":
        code = f"[Server]\nYour friend code:\n{hr}\n{f_codes[user]}\n{hr}"
        cs.send(encrypt(code.encode("utf-8")))

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((SERVER_HOST, SERVER_PORT))
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

while True:
    cli_socket, cli_addr = s.accept()
    print(f"[+] {cli_addr} connected.")

    first_resp = cli_socket.recv(1024).decode("utf-8")
    username = ""
    if first_resp == "!signup":
        handle_command("!signup".encode("utf-8"), cli_socket)
    else:
        username = first_resp
    username = cli_socket.recv(1024).decode("utf-8") if not username else username

    if username in users and username not in authenticated_users:
        password = users[username]["passw"]
        salt = users[username]["salt"]
        challenge = encrypt("OK".encode("utf-8"), password)       
        challenge_string = f"{b64encode(salt).decode("utf-8")}|{b64encode(challenge).decode("utf-8")}"
        cli_socket.send(encrypt(challenge_string.encode("utf-8")))

        response = cli_socket.recv(1024).decode("utf-8")
        if response == "OK":
            client_sockets.add(cli_socket)
            authenticated_users.append(username)
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
