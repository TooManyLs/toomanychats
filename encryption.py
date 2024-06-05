from base64 import b64decode, b64encode
import json

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2

def generate_key(passw: str, salt: bytes, lenght: int = 32) -> bytes:
    return PBKDF2(passw, salt, dkLen=lenght, count=1000000)

def generate_sha256() -> str:
    rand = get_random_bytes(32)
    hash_obj = SHA256.new()
    hash_obj.update(rand)
    hex_hash = hash_obj.hexdigest()
    return hex_hash

def encrypt_aes(msg: bytes, key: bytes | None = None) -> tuple[bytes, bytes]:
    iv = get_random_bytes(16)
    key = get_random_bytes(32) if not key else key
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_msg = pad(msg, AES.block_size)
    return iv + cipher.encrypt(padded_msg), key

def decrypt_aes(msg: bytes, key: bytes) -> bytes:
    iv = msg[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_message = cipher.decrypt(msg[16:])
    return unpad(decrypted_message, AES.block_size)

def send_encrypted(msg, pubkey):
    try:
        pubkey = RSA.import_key(pubkey)
    except:
        pass
    cipher = PKCS1_OAEP.new(pubkey)
    text, key = msg
    pubkey_bytes = pubkey.export_key()
    return json.dumps((
        b64encode(text).decode('utf-8'), 
        b64encode(cipher.encrypt(key)).decode('utf-8'), 
        pubkey_bytes.decode('utf-8')
        ))

def recv_encrypted(msg):
    text, aes, pub = json.loads(msg)
    return (
        b64decode(text.encode('utf-8')), 
        b64decode(aes.encode('utf-8')), 
        RSA.import_key(pub.encode('utf-8'))
    )

def pack_data(msg: tuple[bytes, bytes], public_key: bytes) -> bytes:
    pubkey = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(pubkey)
    text, key = msg
    data: bytes = text + b'<SEP>' + cipher.encrypt(key) + b'<SEP>' + public_key
    return data

def unpack_data(msg: bytes) -> tuple[bytes, bytes, RsaKey]:
    text, aes, pub = msg.split(b'<SEP>')
    data: tuple[bytes, bytes, RsaKey] = text, aes, RSA.import_key(pub)
    return data