import pytest

from config import Settings
from models.errors import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError
from services.processing.validation import validate_upload
from tests.conftest import image_bytes, make_settings, upload_file

HEIC_HEADER = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 300
SVG_DOCUMENT = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'


async def validate(filename: str, data: bytes, content_length: int | None = None, settings: Settings | None = None):
    return await validate_upload(upload_file(filename, data), content_length, settings or make_settings())


@pytest.mark.parametrize(
    ("filename", "image_format", "mime_type"),
    [("photo.jpg", "JPEG", "image/jpeg"), ("photo.png", "PNG", "image/png")],
)
async def test_supported_images_are_accepted(filename: str, image_format: str, mime_type: str):
    data = image_bytes(image_format)
    validated = await validate(filename, data)
    assert validated.kind == "image"
    assert validated.mime_type == mime_type
    assert validated.size_bytes == len(data)
    assert len(validated.sha256) == 64


@pytest.mark.parametrize(("filename", "mime_type"), [("notes.txt", "text/plain"), ("notes.md", "text/markdown")])
async def test_supported_text_files_are_accepted(filename: str, mime_type: str):
    validated = await validate(filename, "Client notes: black hair, שיער שחור".encode())
    assert validated.kind == "text"
    assert validated.mime_type == mime_type


async def test_extension_and_bytes_must_agree():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("notes.txt", image_bytes("PNG"))
    with pytest.raises(UnsupportedFileTypeError):
        await validate("photo.png", b"just some words")


async def test_unsupported_types_are_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("photo.heic", HEIC_HEADER)
    with pytest.raises(UnsupportedFileTypeError):
        await validate("drawing.svg", SVG_DOCUMENT)


async def test_oversize_file_is_rejected():
    small_limit = make_settings(MAX_TEXT_BYTES=10_000)
    # A tiny body with a big Content-Length shows the header check fires before any byte is read.
    with pytest.raises(FileTooLargeError):
        await validate("big.txt", b"hi", content_length=100_000, settings=small_limit)
    with pytest.raises(FileTooLargeError):
        await validate("big.txt", b"a" * 20_000, settings=small_limit)


async def test_empty_file_is_rejected():
    with pytest.raises(EmptyFileError):
        await validate("empty.txt", b"")


async def test_filename_is_cleaned():
    assert (await validate("../../etc/notes.md", b"hello")).filename == "notes.md"
    assert (await validate("a\nb\x00c.txt", b"hello")).filename == "abc.txt"
    capped = await validate("a" * 1_000 + ".txt", b"hello")
    assert len(capped.filename) == 255
    assert capped.filename.endswith(".txt")
