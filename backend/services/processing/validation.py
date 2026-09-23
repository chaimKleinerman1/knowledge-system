import hashlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Protocol

import filetype
from PIL import Image, UnidentifiedImageError

from config import Settings
from models.asset import AssetKind
from models.errors import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError

ALLOWED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
TEXT_MIME_TYPES_BY_EXTENSION = {".txt": "text/plain", ".md": "text/markdown"}
MAGIC_NUMBER_BYTES = 261
READ_CHUNK_BYTES = 1024 * 1024
# Content-Length covers the whole multipart body, not only the file bytes.
MULTIPART_OVERHEAD_BYTES = 8 * 1024
FALLBACK_FILENAME = "upload"

UNSUPPORTED_TYPE_MESSAGE = "Unsupported file type. Upload a .txt or .md file, or a JPEG, PNG, WebP or GIF image."


class ByteStream(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    kind: AssetKind
    mime_type: str
    content: bytes
    size_bytes: int
    sha256: str


async def validate_upload(
    filename: str | None, content_length: int | None, stream: ByteStream, settings: Settings
) -> ValidatedUpload:
    safe_filename = _safe_filename(filename)
    extension = PurePosixPath(safe_filename).suffix.lower()
    size_limit = settings.MAX_TEXT_BYTES if extension in TEXT_MIME_TYPES_BY_EXTENSION else settings.MAX_IMAGE_BYTES
    if content_length is not None and content_length > size_limit + MULTIPART_OVERHEAD_BYTES:
        raise FileTooLargeError(_too_large_message(settings))

    content = await _read_within_limit(stream, size_limit, settings)
    if not content:
        raise EmptyFileError("The file is empty.")

    detected = filetype.guess(content[:MAGIC_NUMBER_BYTES])
    if detected is None:
        kind: AssetKind = "text"
        mime_type = _validate_text(content, extension)
    else:
        if extension in TEXT_MIME_TYPES_BY_EXTENSION:
            raise UnsupportedFileTypeError("The file name says text, but the content is not text.")
        kind = "image"
        mime_type = _validate_image(content, detected.mime, settings)

    return ValidatedUpload(
        filename=safe_filename,
        kind=kind,
        mime_type=mime_type,
        content=content,
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )


async def _read_within_limit(stream: ByteStream, size_limit: int, settings: Settings) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await stream.read(READ_CHUNK_BYTES)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > size_limit:
            raise FileTooLargeError(_too_large_message(settings))
        chunks.append(chunk)


def _validate_text(content: bytes, extension: str) -> str:
    mime_type = TEXT_MIME_TYPES_BY_EXTENSION.get(extension)
    if mime_type is None:
        raise UnsupportedFileTypeError(UNSUPPORTED_TYPE_MESSAGE)
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise UnsupportedFileTypeError("The text file is not valid UTF-8 text.") from error
    return mime_type


def _validate_image(content: bytes, mime_type: str, settings: Settings) -> str:
    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise UnsupportedFileTypeError(UNSUPPORTED_TYPE_MESSAGE)
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        # verify() only checks the container; load() decodes and catches truncated data.
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
            if max(width, height) > settings.MAX_IMAGE_PIXELS_SIDE:
                raise FileTooLargeError(
                    f"The image is too large. Max {settings.MAX_IMAGE_PIXELS_SIDE} pixels on each side."
                )
            image.load()
    except Image.DecompressionBombError as error:
        raise FileTooLargeError("The image has too many pixels to process safely.") from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise UnsupportedFileTypeError("The image file is damaged or incomplete.") from error
    return mime_type


def _safe_filename(filename: str | None) -> str:
    # Keep only the last path segment so a client cannot smuggle directories into the name.
    name = PurePosixPath((filename or "").replace("\\", "/")).name.strip()
    return name or FALLBACK_FILENAME


def _too_large_message(settings: Settings) -> str:
    image_megabytes = settings.MAX_IMAGE_BYTES // (1024 * 1024)
    text_megabytes = settings.MAX_TEXT_BYTES // (1024 * 1024)
    return f"File is too big. Max {image_megabytes} MB for images, {text_megabytes} MB for text."
