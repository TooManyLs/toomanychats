import socket
from threading import Thread
# from encryption import encrypt, decrypt

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002

client_sockets = set()
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((SERVER_HOST, SERVER_PORT))
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

def listen_for_client(cs):
    while True:
        try:
            msg = cs.recv(1024)
        except (OSError, ConnectionResetError):
            print("Socket is closed.")
            if cs in client_sockets:
                client_sockets.remove(cs)
            cs.close()
            break  # Exit the loop when the client disconnects
        else:
            for cli_socket in list(client_sockets):  # Create a copy for iteration
                try:
                    cli_socket.send(msg)
                except ConnectionResetError:
                    print(f"Client disconnected.")
                    if cli_socket in client_sockets:
                        client_sockets.remove(cli_socket)
                    cli_socket.close()
    
while True:
    cli_socket, cli_addr = s.accept()
    print(f"[+] {cli_addr} connected.")
    client_sockets.add(cli_socket)
    t = Thread(target=listen_for_client, args=(cli_socket,))
    t.daemon = True
    t.start()

for cs in list(client_sockets):
    cs.close()
    client_sockets.remove(cs)
s.close()