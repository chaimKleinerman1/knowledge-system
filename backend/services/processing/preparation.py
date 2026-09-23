import base64
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

THUMBNAIL_SIDE = 1536
JPEG_QUALITY = 85
IMAGE_DATA_URI_PREFIX = "data:image/jpeg;base64,"
TEXT_HEAD_CHARS = 16000
TEXT_TAIL_CHARS = 4000
TEXT_TRUNCATION_MARKER = "\n...\n"
STORED_TEXT_MAX_CHARS = 200_000


@dataclass(frozen=True)
class PreparedText:
    text: str
    truncated: bool


def prepare_image(content: bytes) -> str:
    """Downscale the image and return it as a JPEG data URI ready for the model."""
    with Image.open(BytesIO(content)) as image:
        rgb_image = image.convert("RGB")
    rgb_image.thumbnail((THUMBNAIL_SIDE, THUMBNAIL_SIDE))
    buffer = BytesIO()
    rgb_image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return IMAGE_DATA_URI_PREFIX + base64.b64encode(buffer.getvalue()).decode("ascii")


def prepare_text(text: str, max_chars: int) -> PreparedText:
    """Keep the start and the end of a long text; the middle is the least informative part."""
    if len(text) <= max_chars:
        return PreparedText(text=text, truncated=False)
    return PreparedText(text=text[:TEXT_HEAD_CHARS] + TEXT_TRUNCATION_MARKER + text[-TEXT_TAIL_CHARS:], truncated=True)


def cap_stored_text(text: str) -> str:
    return text[:STORED_TEXT_MAX_CHARS]
