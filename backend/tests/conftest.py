from io import BytesIO

from fastapi import UploadFile
from PIL import Image

from config import Settings


def make_settings(**overrides: object) -> Settings:
    # Unit tests never open a database; the placeholder URI only satisfies the required field.
    return Settings(_env_file=None, **{"MONGODB_URI": "mongodb://localhost:27017", **overrides})


def upload_file(filename: str, data: bytes) -> UploadFile:
    return UploadFile(BytesIO(data), filename=filename)


def image_bytes(image_format: str, width: int = 64, height: int = 48) -> bytes:
    image = Image.new("RGB", (width, height), color=(200, 30, 30))
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()
