import os
import binascii
from datetime import datetime
import tempfile
from functools import wraps
from time import perf_counter
import shutil
from io import BytesIO

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

def cache_check(func):
    cache = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key in cache:
            output_path = cache[key]
            if os.path.exists(output_path):
                return output_path
        result = func(*args, **kwargs)
        cache[key] = result
        return result
    return wrapper

@cache_check
def compress_image(image_path: str="", max_size: int=1280, 
                   *, gif_compression: bool=False, temp: bool=False) -> str | QImage:
    if image_path[-4:] == ".gif" and not gif_compression:
        path = f"./cache/img/{generate_name()}.gif"
        shutil.copyfile(image_path, path)
        return path
    if not image_path:
        clipboard = QApplication.clipboard()
        img = clipboard.image()

        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        img.save(buffer, "JPEG")
    if temp:
        _, output_path = tempfile.mkstemp(suffix=".jpg")
    else:
        output_path = f"./cache/img/{generate_name()}.jpg"

    register_heif_opener()
    register_avif_opener()
    with Image.open(image_path if image_path else BytesIO(buffer.data())) as img:
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        max_dim = max(width, height)

        if max_dim > max_size:
            scale_factor = max_size / max_dim

            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            img = img.resize((new_width, new_height), Image.LANCZOS)

        img = img.convert("RGB")
        if image_path:
            img.save(output_path, "JPEG", quality=90)
        else:
            byte_arr = BytesIO()
            img.save(byte_arr, format='JPEG', quality=90)
            byte_arr = byte_arr.getvalue()
            compressed_qimage = QImage.fromData(byte_arr, "JPEG")
            return compressed_qimage

    return output_path

def timer(func):
    def wrapper(*args, **kwargs):
        ts = perf_counter()
        result = func(*args, **kwargs)
        te = perf_counter()
        print(f"{func.__name__} took {te - ts:.3f} seconds to execute.")
        return result
    return wrapper

def secure_delete(filepath: str, passes: int=10) -> None:
    with open(filepath, "ba+") as f:
        length = f.tell()
    with open(filepath, "br+") as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(length))
    os.remove(filepath)