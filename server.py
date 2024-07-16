import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio import IncompleteReadError
import socket
import ssl
from typing import TypedDict

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import pyotp

from database import Connect, NoDataFoundError
from encryption import (encrypt_aes, decrypt_aes, generate_sha256, 
                        pack_data, unpack_data,)

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile='ssl/cert.pem', 
                            keyfile='ssl/private_key.pem')
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3  

SERVER_RSA = RSA.generate(2048)
s_cipher = PKCS1_OAEP.new(SERVER_RSA)

default_code = {
    "admin":\
    generate_sha256()}
print("default_code=", default_code["admin"])

class UserInfo(TypedDict):
    sock: StreamWriter
    public_key: bytes
    friend_code: str

class UserAuthInfo(TypedDict):
    password: bytes
    salt: bytes
    secret: str
    user_pub: bytes
    new_device: bool

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
    try:
        data_length_bytes = await reader.readexactly(4)
    except IncompleteReadError:
        return b''
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
    commands = {
        "/code": lambda: send_fcode(writer, username)
    }
    
    with Connect() as db:
        while True:
            try:
                data = await receive_chunks(reader)
                if not data:
                    raise ConnectionResetError
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
                await commands[cmd]()
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
    with Connect() as db:
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
            name, passw, salt, secret, device_id, pubkey = reg_info.split(b"<SEP>")
            name = name.decode()
            secret = secret.decode()
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
                    secret,
                    device_id,
                    pubkey
                )
                break

async def secure_connect(writer: StreamWriter) -> tuple[str, int] | None:
    """Sends SSL certificate copy to a client for comparison or obtaining
    and starts TLS v1.3 connection.

    :param writer:
    :type writer: ```StreamWriter```
    :return: returns client's peername tuple (IP address and port) if secure connection established else ```None```
    :rtype: ```tuple[str, int] | None```
    """

    cli_addr = writer.get_extra_info('peername')
    print(f"[!] {cli_addr[0]}:{cli_addr[1]} tries to connect.")

    # Sending copy of certificate to the client
    with open("./ssl/cert.pem", "rb") as f:
        cert = f.read()
    writer.write(len(cert).to_bytes(4, "big"))
    await writer.drain()
    writer.write(cert)

    try:
        await writer.start_tls(ssl_context)
        print(f"[+] {cli_addr[0]}:{cli_addr[1]} secure connection established.")
        return cli_addr
    except ConnectionResetError:
        print(f"[-] {cli_addr[0]}:{cli_addr[1]} can't establish secure connection.")
        writer.close()
        return
    
async def check_user(writer: StreamWriter, reader: StreamReader, 
                     username: str, d_id: bytes, cli_addr: tuple[str, int], 
                     db: Connect) -> UserAuthInfo | None:
    if username in auth_users:
        print(f"[-] {cli_addr} tries to connect as {username}")
        writer.write("failed".encode())
        return
    try:
        user = db.get_user(username, d_id)
    except NoDataFoundError:
        print(f"[-] No such user as {username}.")
        writer.write("failed".encode())
        return

    # Get user's public RSA key
    new_device = False
    if user[1] == "0":
        new_device = True
        writer.write(b"new device")
        user_pub = await reader.read(2048)
    else:
        # TODO: Handle lost RSA keys.
        user_pub = user[1].encode()

    return UserAuthInfo(
        password=user[0]["password"],
        salt=user[0]["salt"],
        secret=user[0]["totp_secret"],
        user_pub=user_pub,
        new_device=new_device
    )

async def handle_client(reader: StreamReader, writer: StreamWriter) -> None:
    cli_addr = await secure_connect(writer)
    if cli_addr is None:
        return

    writer.write(SERVER_RSA.public_key().export_key())

    with Connect() as db:
        while True:
            data = await reader.read(1024)
            if not data:
                print(f"[-] {cli_addr[0]}:{cli_addr[1]} disconnected.")
                writer.close()
                break
            if data == b"/signup":
                await sign_up(reader, writer)
                continue
            username, device_id = data.split(b"<SEP>")
            username = username.decode()

            user = await check_user(writer, reader, username, 
                                    device_id, cli_addr, db)
            if user is None:
                continue

            user_pub = user["user_pub"]

            # Challenge user
            challenge, _ = encrypt_aes(b"OK", user["password"])
            challenge_string = b"<SEP>".join([user["salt"], challenge])
            writer.write(pack_data(encrypt_aes(challenge_string), user_pub))
            response = await reader.read(1024)
            if response != b"OK":
                print(f"[-] {username} failed to authenticate [wrong password].")
                continue

            if not await verify_totp(reader, writer, user["secret"]):
                return

            if user["new_device"]:
                db.add_device(username, device_id, user_pub.decode())

            auth_users[username] = UserInfo(
                sock=writer, 
                public_key=user_pub, 
                friend_code=generate_sha256()
                )
            writer.write(b"success")
            asyncio.create_task(listen_for_client(reader, writer, username))
            break

async def verify_totp(reader: StreamReader, writer: StreamWriter, secret: str) -> bool:
    totp = pyotp.TOTP(secret)
    while True:
        otp = await reader.read(6)
        if not otp:
            writer.close()
            return False
        if not totp.verify(otp.decode()):
            writer.write(b"failed")
            continue
        else:
            return True


async def main() -> None:
    server = await asyncio.start_server(
        handle_client, SERVER_HOST, SERVER_PORT,
        family=socket.AF_INET, 
        reuse_address=True)

    addr = server.sockets[0].getsockname()
    print(f"[*] Listening on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())