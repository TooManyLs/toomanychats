import os
import binascii
from datetime import datetime

def generate_name():
    dust = binascii.hexlify(os.urandom(8)).decode()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{dust}_{timestamp}"