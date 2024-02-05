from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

key = b"chipichapa228dibidibidabadaba123"

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