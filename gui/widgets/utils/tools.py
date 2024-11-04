import os
from pathlib import Path
import platform
import binascii
from datetime import datetime
from functools import wraps
from time import perf_counter
from io import BytesIO
from collections import OrderedDict
from hashlib import sha256

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener, register_avif_opener
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtCore import QBuffer

def generate_name() -> str:
    """Generates random name with timestamp"""
    dust = binascii.hexlify(os.urandom(8)).decode()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{dust}_{timestamp}"

def get_device_id(name: str) -> bytes:
    device = platform.uname()
    system = device.system
    node = device.node
    machine = device.machine

    device_str = f"{system}{node}{machine}{name}".encode('utf-8')

    return sha256(device_str).digest()

def cache_check(max_size: int):
    def decorator(func):
        cache = OrderedDict()
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            if key in cache:
                # Move the accessed key to the end of the OrderedDict
                cache.move_to_end(key)
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            # If the cache has exceeded max_size, remove the oldest item
            if len(cache) > max_size:
                cache.popitem(last=False)
            return result
        return wrapper
    return decorator

@cache_check(max_size=64)
def compress_image(image_path: str="", max_size: int = 1280) -> QImage:
    if not image_path:
        clipboard = QApplication.clipboard()
        img = clipboard.image()

        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        img.save(buffer, "JPEG")
        byte_arr = buffer.data().data()
    else:
        with open(image_path, 'rb') as f:
            byte_arr = f.read()

    register_heif_opener()
    register_avif_opener()
    with Image.open(BytesIO(byte_arr)) as img:
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        max_dim = max(width, height)

        if max_dim > max_size:
            scale_factor = max_size / max_dim

            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            img = img.resize((new_width, new_height), Image.LANCZOS)

        img = img.convert("RGB")
        byte_arr = BytesIO()
        img.save(byte_arr, format='JPEG', quality=90 if max_size > 128 else 30)
        byte_arr = byte_arr.getvalue()
        compressed_qimage = QImage.fromData(byte_arr, "JPEG")

    return compressed_qimage

def qimage_to_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    image.save(buffer, "JPEG")
    bytes_data = buffer.data().data()
    return bytes_data

def timer(func):
    def wrapper(*args, **kwargs):
        ts = perf_counter()
        result = func(*args, **kwargs)
        te = perf_counter()
        print(f"{func.__name__} took {te - ts:.3f} seconds to execute.")
        return result
    return wrapper

def get_documents_dir() -> Path:
    """Returns a path to a Documents directory.
    Creates one if it didn't exist."""

    documents_dir = Path(os.path.expanduser("~/Documents"))
    documents_dir.mkdir(parents=True, exist_ok=True)

    return documents_dir
