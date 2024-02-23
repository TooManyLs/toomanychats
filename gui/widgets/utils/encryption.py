from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2
from base64 import b64decode, b64encode
import json

def generate_key(passw, salt, lenght=32):
    return PBKDF2(passw, salt, dkLen=lenght, count=1000000)

def generate_sha256():
    rand = get_random_bytes(32)
    hash_obj = SHA256.new()
    hash_obj.update(rand)
    hex_hash = hash_obj.hexdigest()
    return hex_hash

def encrypt_aes(msg, key=None):
    iv = get_random_bytes(16)
    key = get_random_bytes(32) if not key else key
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_msg = pad(msg, AES.block_size)
    return iv + cipher.encrypt(padded_msg), key

def decrypt_aes(msg, key):
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
