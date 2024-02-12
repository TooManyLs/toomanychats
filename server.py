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
import asyncio

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

async def listen_for_client(reader, writer, username):
    while True:
        try:
            data = await reader.read(10000)
            msg = data.decode('utf-8')
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
                            pubkey = users[name]["public"]
                            client.write(send_encrypted(
                                (msg, dec_key), pubkey
                                ).encode('utf-8'))
                else:
                    cli = ""
                    for user, sub_dict in users.items():
                        if sub_dict['public'] == pub.export_key():
                            cli = authenticated_users[user]
                            cli.write(send_encrypted((msg, aes), pub).encode('utf-8'))
                            break
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

async def handle_command(cmd, reader, writer, user=None):
    hr = "-" * 80
    if cmd == "!signup":
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
        if name not in users:
            writer.write(f"[+] You've successfully created an account!".encode('utf-8'))
            f_codes[friend] = generate_sha256()
            pubkey = pubkey.strip()
            users[name] = {
                "passw": b64decode(passw.encode('utf-8')), 
                "salt": b64decode(salt),
                "public": pubkey.encode('utf-8')
            }
        else:
            writer.write(f"[-] {name} is not available.".encode('utf-8'))
            pass
    elif cmd == "!userlist":
        user_pub = users[user]["public"]
        userlist =\
         f"[Server]\nUser list:\n{hr}\n{"\n".join(authenticated_users.keys())}\n{hr}"
        writer.write(send_encrypted(encrypt_aes(userlist.encode('utf-8')), user_pub)\
                .encode('utf-8'))
    elif cmd == "!code":
        code = f"[Server]\nYour friend code:\n{hr}\n{f_codes[user]}\n{hr}"
        user_pub = users[user]["public"]
        writer.write(send_encrypted(encrypt_aes(code.encode('utf-8')), user_pub)\
                .encode('utf-8'))

import asyncio

async def handle_client(reader, writer):
    cli_addr = writer.get_extra_info('peername')
    print(f"[+] {cli_addr} connected.")
    writer.write(SERVER_RSA.public_key().export_key())
    data = await reader.read(1024)
    first_resp = data.decode('utf-8')
    username = ""
    if first_resp == "!signup":
        await handle_command("!signup", reader, writer)
    else:
        username = first_resp
    data = await reader.read(1024)
    username = data.decode('utf-8') if not username else username

    if username in users and username not in authenticated_users:
        password = users[username]["passw"]
        salt = users[username]["salt"]
        user_pub = users[username]["public"]
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
        else:
            print(f"[-] {username} failed to authenticate.")
            writer.close()
    else:
        print(f"[-] No such user as {username}." if username not in users\
               else f"[-] {cli_addr} tries to connect as {username}")
        writer.close()

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
