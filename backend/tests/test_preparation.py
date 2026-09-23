import base64
from io import BytesIO

from PIL import Image

from services.processing.preparation import (
    IMAGE_DATA_URI_PREFIX,
    TEXT_HEAD_CHARS,
    TEXT_TAIL_CHARS,
    TEXT_TRUNCATION_MARKER,
    prepare_image,
    prepare_text,
)
from tests.conftest import image_bytes


def test_long_text_keeps_its_head_and_tail():
    short = prepare_text("short note", max_chars=20_000)
    assert short.text == "short note"
    assert short.truncated is False

    text = "".join(f"{index:05d} " for index in range(6000))
    prepared = prepare_text(text, max_chars=20_000)
    assert prepared.truncated is True
    assert prepared.text == text[:TEXT_HEAD_CHARS] + TEXT_TRUNCATION_MARKER + text[-TEXT_TAIL_CHARS:]


def test_image_becomes_a_jpeg_data_uri_within_the_thumbnail_box():
    data_uri = prepare_image(image_bytes("PNG", 3000, 2000))
    assert data_uri.startswith(IMAGE_DATA_URI_PREFIX)
    with Image.open(BytesIO(base64.b64decode(data_uri[len(IMAGE_DATA_URI_PREFIX) :]))) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.size == (1536, 1024)
