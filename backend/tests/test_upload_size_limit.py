from collections.abc import AsyncIterator, Iterator

from httpx import ASGITransport, AsyncClient

from ai.fake_client import FakeAiClient
from main import create_app
from services.processing.validation import MULTIPART_OVERHEAD_BYTES
from tests.conftest import make_settings

MAX_IMAGE_BYTES = 50_000
MAX_BODY_BYTES = MAX_IMAGE_BYTES + MULTIPART_OVERHEAD_BYTES
CHUNK_BYTES = 1_000
BOUNDARY = "upload-size-limit-test"
MULTIPART_HEADERS = {"content-type": f"multipart/form-data; boundary={BOUNDARY}"}
BODY_HEAD = f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="file"; filename="big.txt"\r\n\r\n'.encode()
BODY_TAIL = f"\r\n--{BOUNDARY}--\r\n".encode()


class CountingBody:
    """Streams a multipart upload chunk by chunk and remembers how much of it the server pulled."""

    def __init__(self, file_bytes: int) -> None:
        self._file_bytes = file_bytes
        self.sent_bytes = 0

    @property
    def total_bytes(self) -> int:
        return len(BODY_HEAD) + self._file_bytes + len(BODY_TAIL)

    async def chunks(self) -> AsyncIterator[bytes]:
        for chunk in self._pieces():
            self.sent_bytes += len(chunk)
            yield chunk

    def _pieces(self) -> Iterator[bytes]:
        yield BODY_HEAD
        remaining = self._file_bytes
        while remaining > 0:
            piece = min(CHUNK_BYTES, remaining)
            yield b"a" * piece
            remaining -= piece
        yield BODY_TAIL


def make_client() -> AsyncClient:
    # The lifespan is left out on purpose: a rejected upload must never get as far as the database.
    settings = make_settings(MAX_TEXT_BYTES=10_000, MAX_IMAGE_BYTES=MAX_IMAGE_BYTES)
    app = create_app(settings, FakeAiClient(dimensions=8))
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_oversize_content_length_is_rejected_before_any_body_is_read():
    body = CountingBody(file_bytes=MAX_IMAGE_BYTES * 4)
    headers = {**MULTIPART_HEADERS, "content-length": str(body.total_bytes)}
    async with make_client() as client:
        response = await client.post("/api/assets", content=body.chunks(), headers=headers)

    assert response.status_code == 413
    assert "too big" in response.json()["detail"]
    assert response.headers["connection"] == "close"
    assert body.sent_bytes == 0


async def test_chunked_oversize_body_is_cut_off_at_the_limit():
    body = CountingBody(file_bytes=MAX_IMAGE_BYTES * 4)
    async with make_client() as client:
        response = await client.post("/api/assets", content=body.chunks(), headers=MULTIPART_HEADERS)

    assert response.status_code == 413
    assert "too big" in response.json()["detail"]
    assert response.headers["connection"] == "close"
    assert MAX_BODY_BYTES < body.sent_bytes <= MAX_BODY_BYTES + CHUNK_BYTES
    assert body.sent_bytes < body.total_bytes
