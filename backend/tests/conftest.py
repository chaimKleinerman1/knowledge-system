import struct
import zlib
from io import BytesIO

import pytest
from PIL import Image

from config import Settings


class MemoryStream:
    """Minimal async byte stream with the read(size) shape of an UploadFile."""

    def __init__(self, data: bytes) -> None:
        self._buffer = BytesIO(data)

    async def read(self, size: int = -1) -> bytes:
        return self._buffer.read(size)


class UntouchableStream:
    """Fails the test if anything reads it; used to prove a check happens before reading."""

    async def read(self, size: int = -1) -> bytes:
        raise AssertionError("The stream must not be read")


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def image_bytes(image_format: str, width: int = 64, height: int = 48, mode: str = "RGB") -> bytes:
    image = Image.new(mode, (width, height), color=(200, 30, 30) if mode == "RGB" else (200, 30, 30, 128))
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def decompression_bomb_png() -> bytes:
    """A valid PNG header that claims 30000 x 30000 pixels with no pixel data behind it."""

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        body = chunk_type + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", 30000, 30000, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")


@pytest.fixture
def settings() -> Settings:
    return make_settings()
