import socket
from threading import Thread
from encryption import encrypt, generate_key

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002

users = {
    "f": "1234",
    "jiggy": "1111",
    "AssDestroyer": "dadaya",
    "chugga": "4321",
    "bbgirl": "cutie123",
}

client_sockets = set()
authenticated_users = []

def listen_for_client(cs, username):
    while True:
        try:
            msg = cs.recv(1024)
            try:
                if msg.decode("utf-8"):
                    handle_command(msg, cs)
                    continue
            except:
                pass
            if not msg:
                break
            for client in client_sockets:
                if client != cs:
                    client.send(msg)
        except (OSError, ConnectionResetError):
            print("Socket is closed.")
            if cs in client_sockets:
                client_sockets.remove(cs)
            authenticated_users.remove(username)
            cs.close()
            break

def handle_command(cmd, cs):
    hr = "-" * 50
    if cmd.decode("utf-8") == "!userlist":
        users = f"[Server]\nUser list:\n{hr}\n{"\n".join(authenticated_users)}\n{hr}"
        cs.send(encrypt(users.encode("utf-8")))

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((SERVER_HOST, SERVER_PORT))
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

while True:
    cli_socket, cli_addr = s.accept()
    print(f"[+] {cli_addr} connected.")

    username = cli_socket.recv(1024).decode("utf-8")

    if username in users and username not in authenticated_users:
        password = users[username].encode("utf-8")
        challenge = encrypt("OK".encode("utf-8"), generate_key(password, b"chupa"))
        cli_socket.send(challenge)

        response = cli_socket.recv(1024).decode("utf-8")

        if response == "OK":
            client_sockets.add(cli_socket)
            authenticated_users.append(username)
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
