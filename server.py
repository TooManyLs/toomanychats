import socket
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
import asyncio
import database as db

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002
SERVER_RSA = RSA.generate(2048)
s_cipher = PKCS1_OAEP.new(SERVER_RSA)
db_pass = input("input database password: ")

f_codes = {
    "admin":\
    "A408DB8643628EAC4C6474814F347EEA06EB51BE8108D3C461EE5DADE74A17ED"}

client_sockets = set()
authenticated_users = {}

async def listen_for_client(reader, writer, username):
    conn = db.connect(db_pass)
    while True:
        try:
            data = await reader.read(10000)
            msg = data.decode('utf-8')
            if not msg:
                raise ConnectionResetError
            try:
                msg, aes, pub = recv_encrypted(msg)
                if pub == SERVER_RSA.public_key():
                    dec_key = s_cipher.decrypt(aes)
                    for client in client_sockets:
                        if client != writer:
                            name = ""
                            for user, sock in authenticated_users.items():
                                if sock == client:
                                    name = user
                                    break
                            user = db.get_user(conn, name, "public_key")
                            pubkey = user["public_key"].encode('utf-8')
                            client.write(send_encrypted(
                                (msg, dec_key), pubkey
                                ).encode('utf-8'))
                else:
                    user = db.get_by_pubkey(conn, pub.export_key().decode('utf-8'))
                    cli = authenticated_users[user]
                    cli.write(send_encrypted(msg, aes), pub).encode('utf-8')
                    continue
            except Exception as e:
                await handle_command(msg, reader, writer, username)
                continue
        except (OSError, ConnectionResetError):
            print("Socket is closed.")
            if writer in client_sockets:
                client_sockets.remove(writer)
            del authenticated_users[username]
            del f_codes[username]
            writer.close()
            break
    conn.close()

async def handle_command(cmd, reader, writer, username=None):
    conn = db.connect(db_pass)
    hr = "-" * 80
    if cmd == "/signup":
        try:
            data = await reader.read(1024)
            friend_code, friend = data.decode('utf-8').split("|")
            if f_codes[friend] == friend_code:
                writer.write("approve".encode('utf-8'))
        except (KeyError, ValueError):
            writer.write("reject".encode('utf-8'))
            return  
        data = await reader.read(2048)
        reg_info = data.decode('utf-8')
        reg_info, aes, pub = recv_encrypted(reg_info)
        aes = s_cipher.decrypt(aes)
        reg_info = decrypt_aes(reg_info, aes).decode('utf-8')
        name, passw, salt, pubkey = reg_info.split("|")
        if db.get_user(conn, name, "name") is None:
            writer.write(f"[+] You've successfully created an account!".encode('utf-8'))
            f_codes[friend] = generate_sha256()
            db.add_user(
                conn,
                name,
                b64decode(passw.encode('utf-8')),
                b64decode(salt),
                pubkey.encode('utf-8')
            )
        else:
            writer.write(f"[-] {name} is not available.".encode('utf-8'))
            pass
    elif cmd == "/userlist":
        user = db.get_user(conn, username, "public_key")
        user_pub = user["public_key"].encode('utf-8')
        userlist =\
         f"[Server]\nUser list:\n{hr}\n{"\n".join(authenticated_users.keys())}\n{hr}"
        writer.write(send_encrypted(encrypt_aes(userlist.encode('utf-8')), user_pub)\
                .encode('utf-8'))
    elif cmd == "/code":
        code = f"[Server]\nYour friend code:\n{hr}\n{f_codes[username]}\n{hr}"
        user = db.get_user(conn, username, "public_key")
        user_pub = user["public_key"].encode('utf-8')
        writer.write(send_encrypted(encrypt_aes(code.encode('utf-8')), user_pub)\
                .encode('utf-8'))
    conn.close()

async def handle_client(reader, writer):
    conn = db.connect(db_pass)
    cli_addr = writer.get_extra_info('peername')
    print(f"[+] {cli_addr} connected.")
    writer.write(SERVER_RSA.public_key().export_key())
    while True:
        data = await reader.read(1024)
        first_resp = data.decode('utf-8')
        if not first_resp:
            writer.close()
            break
        username = ""
        if first_resp == "/signup":
            await handle_command("/signup", reader, writer)
        else:
            username = first_resp
        if not username:
            data = await reader.read(2048)
            username = data.decode('utf-8')
        user = db.get_user(conn, username)
        if user and username not in authenticated_users:
            password = user["password"]
            salt = user["salt"]
            user_pub = user["public_key"].encode('utf-8')
            challenge, _ = encrypt_aes("OK".encode('utf-8'), password)       
            challenge_string =\
            f"{b64encode(salt).decode('utf-8')}|{b64encode(challenge).decode('utf-8')}"
            writer.write(send_encrypted(
                encrypt_aes(challenge_string.encode('utf-8')), user_pub
                ).encode('utf-8'))
    
            data = await reader.read(1024)
            response = data.decode('utf-8')
            if response == "OK":
                client_sockets.add(writer)
                authenticated_users[username] = writer
                f_codes[username] = generate_sha256()
                print(f"[+] {username} authenticated successfully.")
                asyncio.create_task(listen_for_client(reader, writer, username))
                break
            else:
                print(f"[-] {username} failed to authenticate.")
        else:
            print(f"[-] No such user as {username}." if user == None\
                   else f"[-] {cli_addr} tries to connect as {username}")
    conn.close()

async def main():
    server = await asyncio.start_server(
        handle_client, SERVER_HOST, SERVER_PORT,
        family=socket.AF_INET, 
        reuse_address=True)

    addr = server.sockets[0].getsockname()
    print(f"[*] Listening on {addr}")

    async with server:
        await server.serve_forever()

    for writer in list(client_sockets):
        writer.close()
        client_sockets.remove(writer)

asyncio.run(main())