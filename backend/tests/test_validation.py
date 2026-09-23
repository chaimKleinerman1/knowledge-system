import pytest

from models.errors import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError
from services.processing.validation import validate_upload
from tests.conftest import MemoryStream, UntouchableStream, decompression_bomb_png, image_bytes, make_settings

HEIC_HEADER = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 300
SVG_DOCUMENT = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'


async def validate(filename: str, data: bytes, settings=None, content_length: int | None = None):
    return await validate_upload(filename, content_length, MemoryStream(data), settings or make_settings())


async def test_png_bytes_named_txt_are_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("notes.txt", image_bytes("PNG"))


async def test_text_named_png_is_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("photo.png", b"just some words")


async def test_truncated_jpeg_is_rejected():
    data = image_bytes("JPEG", 400, 300)
    with pytest.raises(UnsupportedFileTypeError):
        await validate("photo.jpg", data[: len(data) // 2])


async def test_huge_side_png_is_rejected_as_too_large():
    with pytest.raises(FileTooLargeError):
        await validate("wide.png", image_bytes("PNG", 9000, 10), make_settings(MAX_IMAGE_PIXELS_SIDE=8000))


async def test_decompression_bomb_is_rejected_as_too_large():
    with pytest.raises(FileTooLargeError):
        await validate("bomb.png", decompression_bomb_png())


async def test_heic_is_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("photo.heic", HEIC_HEADER)


async def test_svg_is_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("drawing.svg", SVG_DOCUMENT)


async def test_oversize_content_length_is_rejected_before_reading():
    settings = make_settings(MAX_TEXT_BYTES=10_000, MAX_IMAGE_BYTES=50_000)
    with pytest.raises(FileTooLargeError):
        await validate_upload("big.txt", 100_000, UntouchableStream(), settings)


async def test_oversize_stream_is_rejected_by_the_byte_counter():
    settings = make_settings(MAX_TEXT_BYTES=10_000, MAX_IMAGE_BYTES=50_000)
    with pytest.raises(FileTooLargeError):
        await validate("big.txt", b"a" * 20_000, settings, content_length=None)


async def test_oversize_image_uses_the_image_limit():
    settings = make_settings(MAX_TEXT_BYTES=10_000, MAX_IMAGE_BYTES=100)
    with pytest.raises(FileTooLargeError):
        await validate("photo.png", image_bytes("PNG"), settings)


async def test_empty_file_is_rejected():
    with pytest.raises(EmptyFileError):
        await validate("empty.txt", b"")


async def test_non_utf8_text_is_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        await validate("latin.txt", "café".encode("latin-1"))


@pytest.mark.parametrize(
    ("filename", "image_format", "mime_type"),
    [
        ("photo.jpg", "JPEG", "image/jpeg"),
        ("photo.png", "PNG", "image/png"),
        ("photo.webp", "WEBP", "image/webp"),
        ("photo.gif", "GIF", "image/gif"),
    ],
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


async def test_image_extension_does_not_matter_when_magic_bytes_are_valid():
    validated = await validate("holiday.txt.jpeg", image_bytes("JPEG"))
    assert validated.kind == "image"


async def test_filename_keeps_only_the_last_path_segment():
    validated = await validate("../../etc/notes.md", b"hello")
    assert validated.filename == "notes.md"
