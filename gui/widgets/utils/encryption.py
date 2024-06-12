from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
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
    key = get_random_bytes(32) if not key else key
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(msg)
    return bytes(cipher.nonce) + ciphertext + tag, key

def decrypt_aes(encrypted_msg: bytes, key: bytes) -> bytes:
    nonce = encrypted_msg[:16]
    tag = encrypted_msg[-16:]
    ciphertext = encrypted_msg[16:-16]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted_message = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_message

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