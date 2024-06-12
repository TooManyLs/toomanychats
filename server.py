import asyncio
from asyncio.streams import StreamReader, StreamWriter
import socket
import ssl
from typing import TypedDict
from getpass import getpass

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from database import Connect, NoDataFoundError
from encryption import (encrypt_aes, decrypt_aes, generate_sha256, 
                        pack_data, unpack_data,)

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002
SERVER_RSA = RSA.generate(2048)
s_cipher = PKCS1_OAEP.new(SERVER_RSA)
db_pass = getpass("input database password: ")

default_code = {
    "admin":\
    generate_sha256()}
print("default_code=", default_code["admin"])

class UserInfo(TypedDict):
    sock: StreamWriter
    public_key: bytes
    friend_code: str

auth_users: dict[str, UserInfo] = {}

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
                del data
                if pub != SERVER_RSA.public_key():
                    user = db.get_by_pubkey(pub.export_key().decode())
                    cli = auth_users[user]["sock"]
                    cli.write(pack_data((msg, aes), pub.export_key()))
                    continue
                
                dec_key = s_cipher.decrypt(aes)
                for u, info in auth_users.items():
                    if u != username:
                        w = info["sock"]
                        pubkey = info["public_key"]
                        await send_chunks(w, pack_data((msg, dec_key), pubkey))
                del msg
            except ValueError:
                cmd = data.decode()
                commands = {
                    "/code": send_fcode(writer, username)
                }
                await commands[cmd]
                continue
            except TypeError:
                continue
            except (OSError, ConnectionResetError):
                print("Socket is closed.")
                del auth_users[username]
                writer.close()
                break

async def send_fcode(writer: StreamWriter, username: str) -> None:
    code = auth_users[username]["friend_code"]
    user_pub = auth_users[username]["public_key"]
    await send_chunks(
        writer, 
        pack_data(encrypt_aes(code.encode()), user_pub)
        )

async def sign_up(reader: StreamReader, writer: StreamWriter) -> None:
    with Connect(db_pass) as db:
        data = await reader.read(1024)
        if data == b"c":
            return
        friend_code, friend = data.decode().split("|")
        if not (friend_code == default_code["admin"] and friend == "admin"):           
            try:
                if auth_users[friend]["friend_code"] == friend_code:
                    pass
            except (KeyError, ValueError):
                writer.write(b"reject")
                return
        writer.write(b"approve")
        while True:
            data = await reader.read(2048)
            if data.decode == b"c":
                return
            reg_info, aes, pub = unpack_data(data)
            aes = s_cipher.decrypt(aes)
            reg_info = decrypt_aes(reg_info, aes)
            name, passw, salt, pubkey = reg_info.split(b"|")
            name = name.decode()
            pubkey = pubkey.decode()
            if name == "admin": 
                writer.write(b"[-]")
                continue
            try:
                db.get_user(name)
                writer.write(b"[-]")
                continue
            except NoDataFoundError:
                writer.write("[+] You've successfully created an account!"
                            .encode())
                if friend != "admin":
                    auth_users[friend]["friend_code"] = generate_sha256()
                else:
                    default_code["admin"] = generate_sha256()
                db.add_user(
                    name,
                    passw,
                    salt,
                    pubkey
                )
                break
            
async def handle_client(reader: StreamReader, writer: StreamWriter) -> None:
    with Connect(db_pass) as db:
        cli_addr = writer.get_extra_info('peername')
        print(f"[+] {cli_addr[0]}:{cli_addr[1]} connected.")
        writer.write(SERVER_RSA.public_key().export_key())
        while True:
            data = await reader.read(1024)
            first_resp = data.decode()
            if not first_resp:
                print(f"[-] {cli_addr[0]}:{cli_addr[1]} disconnected.")
                writer.close()
                break
            if first_resp == "/signup":
                await sign_up(reader, writer)
                continue
            username = first_resp

            if username in auth_users:
                print(f"[-] {cli_addr} tries to connect as {username}")
                writer.write("failed".encode())
                continue
            try:
                user = db.get_user(username)
            except NoDataFoundError:
                print(f"[-] No such user as {username}.")
                writer.write("failed".encode())
                continue
            password = user["password"]
            salt = user["salt"]
            user_pub = user["public_key"].encode()
            challenge, _ = encrypt_aes(b"OK", password)
            challenge_string = b"|".join([salt, challenge])
            writer.write(pack_data(encrypt_aes(challenge_string), user_pub))
            response = await reader.read(1024)
            if response != b"OK":
                print(f"[-] {username} failed to authenticate.")
                continue
            auth_users[username] = UserInfo(
                sock=writer, 
                public_key=user_pub, 
                friend_code=generate_sha256()
                )
            writer.write(b"success")
            asyncio.create_task(listen_for_client(reader, writer, username))
            break

async def main() -> None:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='ssl/cert.pem', 
                                keyfile='ssl/private_key.pem')
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3  

    server = await asyncio.start_server(
        handle_client, SERVER_HOST, SERVER_PORT,
        family=socket.AF_INET, 
        reuse_address=True,
        ssl=ssl_context)

    addr = server.sockets[0].getsockname()
    print(f"[*] Listening on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())