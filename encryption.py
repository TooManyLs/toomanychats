from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2

key = b"chipichapa228dibidibidabadaba123"

def generate_key(passw, salt, lenght=32):
    return PBKDF2(passw, salt, dkLen=lenght)

def generate_sha256():
    rand = get_random_bytes(32)
    hash_obj = SHA256.new()
    hash_obj.update(rand)
    hex_hash = hash_obj.hexdigest()
    return hex_hash

def encrypt(msg, key=key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_msg = pad(msg, AES.block_size)
    return iv + cipher.encrypt(padded_msg)

def decrypt(msg, key=key):
    iv = msg[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_message = cipher.decrypt(msg[16:])
    return unpad(decrypted_message, AES.block_size)