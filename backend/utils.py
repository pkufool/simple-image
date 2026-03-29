import os
import uuid
from PIL import Image as PILImage
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
COMPRESS_QUALITY = int(os.getenv("IMAGE_COMPRESS_QUALITY", 25))

def generate_uuid():
    return uuid.uuid1().hex

def generate_uuid_filename(unique_id: str):
    return f"{unique_id[20:32]}/{unique_id[8:20]}/{unique_id}"

def compress_image(image_data, file_extension):
    original_size = len(image_data)
    img = PILImage.open(BytesIO(image_data))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    compressed_buffer = BytesIO()
    format = file_extension.upper() if file_extension != 'jpg' else 'JPEG'
    img.save(
        compressed_buffer,
        format=format,
        quality=COMPRESS_QUALITY,
        optimize=True
    )
    compressed_data = compressed_buffer.getvalue()
    compressed_size = len(compressed_data)
    return compressed_data, original_size, compressed_size
