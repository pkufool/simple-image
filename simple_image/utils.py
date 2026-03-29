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

def compress_image(image_data, file_extension, quality=None):
    original_size = len(image_data)
    img = PILImage.open(BytesIO(image_data))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    compressed_buffer = BytesIO()
    image_format = file_extension.upper() if file_extension != 'jpg' else 'JPEG'
    use_quality = max(1, min(95, int(quality if quality is not None else COMPRESS_QUALITY)))

    save_kwargs = {"format": image_format, "optimize": True}
    if image_format in ("JPEG", "WEBP"):
        save_kwargs["quality"] = use_quality
    elif image_format == "PNG":
        # Map quality to PNG's compress_level (0 fast, 9 small).
        save_kwargs["compress_level"] = max(0, min(9, int((100 - use_quality) / 10)))

    img.save(compressed_buffer, **save_kwargs)
    compressed_data = compressed_buffer.getvalue()
    compressed_size = len(compressed_data)
    return compressed_data, original_size, compressed_size
