import os
import binascii
from datetime import datetime
import tempfile

from PIL import Image, ImageOps

def generate_name() -> str:
    """Generates random name with timestamp"""
    dust = binascii.hexlify(os.urandom(8)).decode()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{dust}_{timestamp}"

def compress_image(image_path: str, max_size: int=1280, 
                   *, gif_compression: bool=False, temp: bool=False) -> str:
    if image_path[-4:] == ".gif" and not gif_compression:
        return image_path
    
    if temp:
        output_path = tempfile.mktemp(suffix=".jpg")
    else:
        output_path = f"./cache/img/{generate_name()}.jpg"

    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        max_dim = max(width, height)

        if max_dim > max_size:
            scale_factor = max_size / max_dim

            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            img = img.resize((new_width, new_height), Image.LANCZOS)

        img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=90)
    return output_path