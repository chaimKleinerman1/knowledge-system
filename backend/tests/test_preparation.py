import base64
from io import BytesIO

from PIL import Image

from services.processing.preparation import (
    IMAGE_DATA_URI_PREFIX,
    STORED_TEXT_MAX_CHARS,
    TEXT_HEAD_CHARS,
    TEXT_TAIL_CHARS,
    TEXT_TRUNCATION_MARKER,
    cap_stored_text,
    prepare_image,
    prepare_text,
)
from tests.conftest import image_bytes


def test_short_text_is_kept_whole():
    prepared = prepare_text("short note", max_chars=20_000)
    assert prepared.text == "short note"
    assert prepared.truncated is False


def test_long_text_keeps_head_and_tail():
    text = "".join(f"{index:05d} " for index in range(6000))
    prepared = prepare_text(text, max_chars=20_000)
    assert prepared.truncated is True
    assert prepared.text == text[:TEXT_HEAD_CHARS] + TEXT_TRUNCATION_MARKER + text[-TEXT_TAIL_CHARS:]


def test_text_at_the_limit_is_not_truncated():
    text = "x" * 20_000
    assert prepare_text(text, max_chars=20_000).truncated is False


def test_stored_text_is_capped():
    assert len(cap_stored_text("y" * (STORED_TEXT_MAX_CHARS + 10))) == STORED_TEXT_MAX_CHARS


def test_image_becomes_a_jpeg_data_uri_within_the_thumbnail_box():
    data_uri = prepare_image(image_bytes("PNG", 3000, 2000))
    assert data_uri.startswith(IMAGE_DATA_URI_PREFIX)
    with Image.open(BytesIO(base64.b64decode(data_uri[len(IMAGE_DATA_URI_PREFIX) :]))) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.size == (1536, 1024)


def test_small_image_is_not_upscaled():
    data_uri = prepare_image(image_bytes("GIF", 64, 48))
    with Image.open(BytesIO(base64.b64decode(data_uri[len(IMAGE_DATA_URI_PREFIX) :]))) as thumbnail:
        assert thumbnail.size == (64, 48)


def test_transparent_image_converts_to_jpeg():
    data_uri = prepare_image(image_bytes("PNG", 80, 80, mode="RGBA"))
    assert data_uri.startswith(IMAGE_DATA_URI_PREFIX)
