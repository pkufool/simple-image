import os
import uuid
from PIL import Image as PILImage
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
COMPRESS_QUALITY = int(os.getenv("IMAGE_COMPRESS_QUALITY", 25))

IMAGE_EXTENSION_ALIASES = {
    "jpg": "jpeg",
    "jpe": "jpeg",
    "jfif": "jpeg",
}

IMAGE_FORMAT_MAP = {
    "jpeg": "JPEG",
    "png": "PNG",
    "gif": "GIF",
    "webp": "WEBP",
}

FORMAT_EXTENSION_MAP = {
    "JPEG": "jpeg",
    "PNG": "png",
    "GIF": "gif",
    "WEBP": "webp",
}

def generate_uuid():
    return uuid.uuid1().hex

def generate_uuid_filename(unique_id: str):
    return f"{unique_id[20:32]}/{unique_id[8:20]}/{unique_id}"


def normalize_image_extension(file_extension: str) -> str:
    ext = (file_extension or "").strip().lower()
    return IMAGE_EXTENSION_ALIASES.get(ext, ext)


def detect_image_extension(image_data: bytes) -> str:
    try:
        image = PILImage.open(BytesIO(image_data))
        image_format = (image.format or "").upper()
    except Exception as exc:
        raise ValueError("Invalid image file") from exc

    extension = FORMAT_EXTENSION_MAP.get(image_format)
    if not extension:
        raise ValueError(f"Unsupported image format: {image_format or 'unknown'}")
    return extension

def compress_image(image_data, file_extension, quality=None):
    original_size = len(image_data)
    img = PILImage.open(BytesIO(image_data))
    normalized_extension = normalize_image_extension(file_extension)
    image_format = IMAGE_FORMAT_MAP.get(normalized_extension)
    if not image_format:
        raise ValueError(f"Unsupported image extension: {file_extension}")

    if image_format == "JPEG" and img.mode not in ("RGB", "L"):
        # JPEG does not support alpha channels.
        img = img.convert("RGB")

    compressed_buffer = BytesIO()
    use_quality = max(1, min(95, int(quality if quality is not None else COMPRESS_QUALITY)))

    save_kwargs = {"format": image_format}
    if image_format in ("JPEG", "PNG"):
        save_kwargs["optimize"] = True

    if image_format in ("JPEG", "WEBP"):
        save_kwargs["quality"] = use_quality
    elif image_format == "PNG":
        # Map quality to PNG's compress_level (0 fast, 9 small).
        save_kwargs["compress_level"] = max(0, min(9, int((100 - use_quality) / 10)))

    img.save(compressed_buffer, **save_kwargs)
    compressed_data = compressed_buffer.getvalue()
    compressed_size = len(compressed_data)
    return compressed_data, original_size, compressed_size


def create_thumbnail(image_data: bytes, size: int = 160, quality: int = 75) -> bytes:
    image = PILImage.open(BytesIO(image_data))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    target_size = max(48, min(512, int(size)))
    try:
        resampling = PILImage.Resampling.LANCZOS
    except AttributeError:
        resampling = PILImage.LANCZOS

    image.thumbnail((target_size, target_size), resample=resampling)

    buffer = BytesIO()
    save_quality = max(40, min(95, int(quality)))
    image.save(
        buffer,
        format="JPEG",
        quality=save_quality,
        optimize=True,
        progressive=True,
    )
    return buffer.getvalue()
