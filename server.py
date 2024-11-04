import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio import IncompleteReadError
from configparser import ConfigParser
import os
import socket
import ssl
from pathlib import Path
from typing import TypedDict
from uuid import UUID

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import pyotp

from database import Connect, NoDataFoundError
from gui.widgets.utils.encryption import (
    encrypt_aes, decrypt_aes, generate_sha256,
    pack_data, unpack_data,
)
from gui.widgets.message import (
        ChunkSize,
        AsyncSender,
        AsyncReceiver,
        Tags,
        MsgType,
        )
from generate_ssl_tls import generate_cert, check_cert
from gui.widgets.utils.tools import get_documents_dir


buffer_limit = ChunkSize.K256

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5002

server_dir = Path(f"{get_documents_dir()}/toomanychats/server")
server_dir.mkdir(parents=True, exist_ok=True)
ssl_dir = Path(f"{server_dir}/ssl")
cert_path = f"{ssl_dir}/cert.pem"
cert_key_path = f"{ssl_dir}/private_key.pem"

if not check_cert(cert_path):
    generate_cert()

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile=cert_path, 
                            keyfile=cert_key_path)
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

config = ConfigParser()
with open(f'{server_dir}/server.conf.enc', 'rb') as f:
    cfg_enc = f.read()
    key = input('Enter encryption key: ').rjust(16, '0')[:16]
    cfg_dec = decrypt_aes(cfg_enc, key=key.encode())
    config.read_string(cfg_dec.decode())

passwd = config.get('Database', 'DB_PASSWORD')
db_name = config.get('Database', 'DB_NAME')

async def listen_for_client(reader: StreamReader, writer: StreamWriter, 
                            username: str) -> None:
    receiver = AsyncReceiver(reader, s_cipher, buffer_limit)
    sender = AsyncSender(buffer_limit)

    commands = {
            "code": send_fcode
            }
 
    with Connect(passwd, db_name) as db:
        while True:
            try:
                tags, data = await receiver.receive_message()
                if tags["message_type"] == MsgType.SERVER:
                    cmd = data.decode().split("<SEP>", 1)[1]
                    await commands[cmd](
                            sender, writer, username, tags=tags
                            )
                    continue
                for u, info in auth_users.items():
                    if u != username:
                        w = info["sock"]
                        pubkey = info["public_key"]
                        await sender.send_message(tags, data, w, pubkey)
            except IncompleteReadError:
                # Client disconnects
                print("Socket is closed.")
                del auth_users[username]
                writer.close()
                break

async def send_fcode(
        sender: AsyncSender, writer: StreamWriter,
        username: str, *, tags: Tags
) -> None:
    code = auth_users[username]["friend_code"]
    user_pub = auth_users[username]["public_key"]
    await sender.send_message(tags, f"code<SEP>{code}".encode(), writer, user_pub)
 
async def check_fcode(reader: StreamReader, writer: StreamWriter) -> str | None:
    while True:
        data = await reader.read(1024)
        if data == b"c":
            return
        friend_code, friend = data.decode().split("|")
        if friend_code == default_code["admin"] and friend == "admin":
            break

        try:
            if auth_users[friend]["friend_code"] == friend_code:
                break
        except (KeyError, ValueError):
            writer.write(b"reject")
            continue
    writer.write(b"approve")

    return friend

async def sign_up(reader: StreamReader, writer: StreamWriter) -> None:
    friend = await check_fcode(reader, writer)
    if not friend:
        return

    with Connect(passwd, db_name) as db:
        while True:
            data = await reader.read(2048)
            if not data or data == b"c":
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
    :return: returns client's peername tuple (IP address and port) 
    if secure connection established else ```None```
    :rtype: ```tuple[str, int] | None```
    """

    cli_addr = writer.get_extra_info('peername')
    print(f"[!] {cli_addr[0]}:{cli_addr[1]} tries to connect.")

    # Sending copy of certificate to the client
    with open(f"{ssl_dir}/cert.pem", "rb") as f:
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

    with Connect(passwd, db_name) as db:
        while True:
            data = await reader.read(1024)
            if not data:
                print(f"[-] {cli_addr[0]}:{cli_addr[1]} disconnected.")
                writer.close()
                break
            if data == b"/signup":
                await sign_up(reader, writer)
                continue
            unpacked, aes, _ = unpack_data(data)
            aes = s_cipher.decrypt(aes)
            name_device = decrypt_aes(unpacked, aes)
            
            username, device_id = name_device.split(b"<SEP>")
            username = username.decode()

            user = await check_user(writer, reader, username, 
                                    device_id, cli_addr, db)
            if user is None:
                continue

            user_pub = user["user_pub"]

            # Challenge user
            check_bytestring = os.urandom(32)
            challenge, _ = encrypt_aes(check_bytestring, user["password"])
            challenge_string = b"<SEP>".join([user["salt"], challenge])
            writer.write(pack_data(encrypt_aes(challenge_string), user_pub))
            response = await reader.read(1024)
            if response != check_bytestring:
                writer.write(b"failed")
                print(f"[-] {username} failed to authenticate [wrong password].")
                continue
            writer.write(b"passed")

            if not await verify_totp(reader, writer, user["secret"]):
                writer.write(b"2manyA")
                writer.close()
                return

            if user["new_device"]:
                db.add_device(username, device_id, user_pub.decode())

            auth_users[username] = UserInfo(
                sock=writer, 
                public_key=user_pub, 
                friend_code=generate_sha256()
                )
            writer.write(b"passed")
            asyncio.create_task(listen_for_client(reader, writer, username))
            break

async def verify_totp(reader: StreamReader, writer: StreamWriter, secret: str) -> bool:
    """Waits for TOTP encrypted with itself zero-padded;
    Then it generates current TOTP and pads it to use as a key
    to decrypt incoming TOTP; Wrong key will result in ValueError"""
    totp = pyotp.TOTP(secret)
    attempts = 5
    while attempts != 0:
        attempts -= 1
        otp = await reader.read(38)
        if not otp:
            writer.close()
            break
        verify_otp = totp.now()
        otp_key = verify_otp.rjust(32, "0")
        try:
            received_otp = decrypt_aes(otp, otp_key.encode()).decode()
            return True
        except ValueError:
            if attempts != 0:
                writer.write(b"failed")
    return False


async def main() -> None:
    server = await asyncio.start_server(
        handle_client, SERVER_HOST, SERVER_PORT,
        family=socket.AF_INET, 
        reuse_address=True,
        limit=buffer_limit.value,
    )

    addr = server.sockets[0].getsockname()
    print(f"[*] Listening on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())
