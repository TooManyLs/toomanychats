import asyncio
from asyncio.streams import StreamReader, StreamWriter
import socket
from base64 import b64encode, b64decode
import ssl

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from database import Connect
from encryption import (encrypt_aes, decrypt_aes, generate_sha256, 
                        send_encrypted, recv_encrypted, pack_data, 
                        unpack_data,
                        )

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

async def send_chunks(writer: StreamWriter, data: bytes, 
                      chunk_size: int = 65536) -> None:
    writer.write(len(data).to_bytes(4, 'big'))
    await writer.drain()
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        writer.write(chunk)
        await writer.drain()

async def receive_chunks(reader: StreamReader, 
                         chunk_size: int = 65536) -> bytes:
    data_length_bytes = await reader.readexactly(4)
    if data_length_bytes == b'code':
        return b'/code'
    data_length = int.from_bytes(data_length_bytes, 'big')
    chunks = []
    bytes_read = 0
    while bytes_read < data_length:
        chunk = await reader.read(min(chunk_size, data_length - bytes_read))
        if chunk:
            chunks.append(chunk)
            bytes_read += len(chunk)
        else:
            raise RuntimeError("Socket connection broken")
    return b''.join(chunks)

async def listen_for_client(reader: StreamReader, writer: StreamWriter, 
                            username: str) -> None:
    with Connect(db_pass) as db:
        while True:
            try:
                data = await receive_chunks(reader)
                if not data:
                    break
                msg, aes, pub = unpack_data(data)

                if pub != SERVER_RSA.public_key():
                    user = db.get_by_pubkey(pub.export_key().decode())
                    cli = authenticated_users[user]
                    cli.write(send_encrypted(msg, aes), pub).encode()
                    continue
                
                dec_key = s_cipher.decrypt(aes)
                for u, cli in authenticated_users.items():
                    if u == username or cli == writer:
                        continue
                    pubkey = db.get_pubkey(u)
                    if pubkey:
                        await send_chunks(
                            cli, 
                            pack_data((msg, dec_key), pubkey)
                            )
                del data, msg
            except ValueError:
                msg = data.decode()
                await handle_command(msg, reader, writer, username)
                continue
            except TypeError:
                continue
            except (OSError, ConnectionResetError):
                print("Socket is closed.")
                if writer in client_sockets:
                    client_sockets.remove(writer)
                del authenticated_users[username]
                del f_codes[username]
                writer.close()
                break

async def handle_command(cmd: str, reader: StreamReader, 
                         writer: StreamWriter, username: str = "") -> None:
    with Connect(db_pass) as db:
        hr = "-" * 80
        if cmd == "/signup":
            try:
                data = await reader.read(1024)
                if data.decode() == "c":
                    return
                friend_code, friend = data.decode().split("|")
                if f_codes[friend] == friend_code:
                    writer.write("approve".encode())
            except (KeyError, ValueError):
                writer.write("reject".encode())
                return
            while True:
                data = await reader.read(2048)
                reg_info = data.decode()
                if reg_info == "c":
                    return
                reg_info, aes, pub = recv_encrypted(reg_info)
                aes = s_cipher.decrypt(aes)
                reg_info = decrypt_aes(reg_info, aes).decode()
                name, passw, salt, pubkey = reg_info.split("|")
                if db.get_user(name) is None:
                    writer.write("[+] You've successfully created an account!"
                                 .encode())
                    f_codes[friend] = generate_sha256()
                    db.add_user(
                        name,
                        b64decode(passw.encode()),
                        b64decode(salt),
                        pubkey.encode()
                    )
                    break
                else:
                    writer.write(f"[-] {name} is not available.".encode())
                    continue
        elif cmd == "/userlist":
            user_pub = db.get_pubkey(username)
            userlist =\
             f"[Server]\nUser list:\n{hr}\n{"\n".join(authenticated_users.keys())}\n{hr}"
            writer.write(send_encrypted(encrypt_aes(userlist.encode()), user_pub)\
                    .encode())
        elif cmd == "/code":
            code = f"{f_codes[username]}"
            user_pub = db.get_pubkey(username)
            if user_pub:
                await send_chunks(
                    writer, 
                    pack_data(encrypt_aes(code.encode()), user_pub)
                    )

async def handle_client(reader: StreamReader, writer: StreamWriter) -> None:
    with Connect(db_pass) as db:
        cli_addr = writer.get_extra_info('peername')
        print(f"[+] {cli_addr} connected.")
        writer.write(SERVER_RSA.public_key().export_key())
        while True:
            data = await reader.read(1024)
            first_resp = data.decode()
            if not first_resp:
                writer.close()
                break
            username = ""
            if first_resp == "/signup":
                await handle_command("/signup", reader, writer)
                continue
            elif first_resp == "c":
                continue
            else:
                username = first_resp
            if not username:
                data = await reader.read(2048)
                username = data.decode()
            user = db.get_user(username)
            if user and username not in authenticated_users:
                password = user["password"]
                salt = user["salt"]
                user_pub = user["public_key"].encode()
                challenge, _ = encrypt_aes("OK".encode(), password)       
                challenge_string =\
                f"{b64encode(salt).decode()}|{b64encode(challenge).decode()}"
                writer.write(send_encrypted(
                    encrypt_aes(challenge_string.encode()), user_pub
                    ).encode())

                data = await reader.read(1024)
                response = data.decode()
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
                print(f"[-] No such user as {username}." if user is None\
                       else f"[-] {cli_addr} tries to connect as {username}")
                writer.write("failed".encode())

async def main() -> None:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='ssl/cert.pem', 
                                keyfile='ssl/private_key.pem')   

    server = await asyncio.start_server(
        handle_client, SERVER_HOST, SERVER_PORT,
        family=socket.AF_INET, 
        reuse_address=True,
        ssl=ssl_context)

    addr = server.sockets[0].getsockname()
    print(f"[*] Listening on {addr}")

    async with server:
        await server.serve_forever()

    for writer in list(client_sockets):
        writer.close()
        client_sockets.remove(writer)

asyncio.run(main())