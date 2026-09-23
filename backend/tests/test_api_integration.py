import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from ai.fake_client import FakeAiClient
from config import Settings
from database.assets_repository import AssetsRepository
from database.files_repository import FILES_BUCKET_NAME
from main import create_app
from tests.conftest import image_bytes, make_settings

MONGODB_TEST_URI = os.environ.get("MONGODB_TEST_URI", "")
TEST_DATABASE_NAME = "knowledge_test"
GRIDFS_FILES_COLLECTION = f"{FILES_BUCKET_NAME}.files"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not MONGODB_TEST_URI, reason="MONGODB_TEST_URI is not set"),
]

SALON_NOTES = b"Client notes: long black hair, trim the ends and add a warm colour gloss.\n"
CAR_NOTES = b"Sold the black car today; the buyer paid cash for the car.\n"
HEBREW_NOTE = "שיער שחור ארוך".encode()


@pytest.fixture
def fake_ai() -> FakeAiClient:
    return FakeAiClient(dimensions=32)


@pytest.fixture
def integration_settings() -> Settings:
    return make_settings(
        MONGODB_URI=MONGODB_TEST_URI, MONGODB_DB_NAME=TEST_DATABASE_NAME, AI_CLIENT="fake", MAX_TEXT_BYTES=20_000
    )


@pytest.fixture
async def client(integration_settings: Settings, fake_ai: FakeAiClient) -> AsyncIterator[AsyncClient]:
    mongo_client = AsyncMongoClient(MONGODB_TEST_URI)
    await mongo_client.drop_database(TEST_DATABASE_NAME)
    await mongo_client.close()
    app = create_app(integration_settings, fake_ai)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
            yield http_client


async def upload(client: AsyncClient, filename: str, data: bytes, content_type: str = "application/octet-stream"):
    return await client.post("/api/assets", files={"file": (filename, data, content_type)})


async def test_health_reports_database_ok(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_text_upload_is_analyzed_and_ready(client: AsyncClient):
    response = await upload(client, "hair_salon_notes.md", SALON_NOTES)
    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "text"
    assert body["mime_type"] == "text/markdown"
    assert body["status"] == "ready"
    assert body["error"] is None
    assert body["deduplicated"] is False
    assert body["file_url"] == f"/api/assets/{body['id']}/file"
    assert "black" in body["ai"]["tags"] and "hair" in body["ai"]["tags"]
    assert body["ai"]["lang_code"] == "en"
    assert body["ai"]["prompt_version"] == "v1"
    assert body["extracted_text"] is None


async def test_image_upload_is_analyzed_and_ready(client: AsyncClient):
    response = await upload(client, "black_car.png", image_bytes("PNG"), "image/png")
    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "image"
    assert body["mime_type"] == "image/png"
    assert body["status"] == "ready"
    assert body["ai"]["category"] == "photo"
    assert "car" in body["ai"]["tags"]


async def test_duplicate_upload_returns_the_existing_asset(client: AsyncClient):
    first = (await upload(client, "hair_salon_notes.md", SALON_NOTES)).json()
    response = await upload(client, "copy_of_notes.md", SALON_NOTES)
    assert response.status_code == 200
    body = response.json()
    assert body["deduplicated"] is True
    assert body["id"] == first["id"]
    assert body["filename"] == "hair_salon_notes.md"
    assert (await client.get("/api/assets")).json()["total"] == 1


async def test_ai_failure_marks_the_asset_failed_and_reprocess_recovers(client: AsyncClient, fake_ai: FakeAiClient):
    fake_ai.fail_describe = True
    response = await upload(client, "hair_salon_notes.md", SALON_NOTES)
    assert response.status_code == 201
    failed = response.json()
    assert failed["status"] == "failed"
    assert failed["error"]
    assert failed["ai"] is None

    fake_ai.fail_describe = False
    response = await client.post(f"/api/assets/{failed['id']}/reprocess")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["error"] is None


async def test_duplicate_upload_of_a_failed_asset_reprocesses_it(client: AsyncClient, fake_ai: FakeAiClient):
    fake_ai.fail_describe = True
    failed = (await upload(client, "hair_salon_notes.md", SALON_NOTES)).json()
    fake_ai.fail_describe = False
    response = await upload(client, "hair_salon_notes.md", SALON_NOTES)
    assert response.status_code == 200
    assert response.json()["id"] == failed["id"]
    assert response.json()["deduplicated"] is True
    assert response.json()["status"] == "ready"


async def test_list_is_newest_first_without_heavy_fields(client: AsyncClient):
    first = (await upload(client, "hair_salon_notes.md", SALON_NOTES)).json()
    second = (await upload(client, "car.txt", CAR_NOTES)).json()
    response = await client.get("/api/assets", params={"limit": 10, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == [second["id"], first["id"]]
    assert all(item["extracted_text"] is None for item in body["items"])
    assert all(item["ai"]["text_content"] is None for item in body["items"])


async def test_detail_includes_extracted_text(client: AsyncClient):
    created = (await upload(client, "hair_salon_notes.md", SALON_NOTES)).json()
    response = await client.get(f"/api/assets/{created['id']}")
    assert response.status_code == 200
    assert response.json()["extracted_text"] == SALON_NOTES.decode()


async def test_unknown_and_malformed_ids_are_not_found(client: AsyncClient):
    assert (await client.get("/api/assets/64b000000000000000000000")).status_code == 404
    assert (await client.get("/api/assets/not-an-id")).status_code == 404
    assert (await client.get("/api/assets/not-an-id/file")).status_code == 404
    assert (await client.post("/api/assets/not-an-id/reprocess")).status_code == 404
    assert (await client.delete("/api/assets/not-an-id")).status_code == 404


async def test_file_bytes_round_trip(client: AsyncClient):
    data = image_bytes("JPEG", 120, 90)
    created = (await upload(client, "photo one.jpg", data, "image/jpeg")).json()
    response = await client.get(f"/api/assets/{created['id']}/file")
    assert response.status_code == 200
    assert response.content == data
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["content-disposition"].startswith('inline; filename="photo one.jpg"')


async def test_delete_removes_the_asset_and_its_file(client: AsyncClient):
    created = (await upload(client, "hair_salon_notes.md", SALON_NOTES)).json()
    assert (await client.delete(f"/api/assets/{created['id']}")).status_code == 204
    assert (await client.get(f"/api/assets/{created['id']}")).status_code == 404
    assert (await client.get(f"/api/assets/{created['id']}/file")).status_code == 404
    assert (await client.get("/api/assets")).json()["total"] == 0


async def test_search_ranks_the_phrase_hit_above_the_or_only_hit(client: AsyncClient):
    await upload(client, "car.txt", CAR_NOTES)
    await upload(client, "hair_salon_notes.md", SALON_NOTES)
    response = await client.get("/api/search", params={"q": "black hair"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "black hair"
    filenames = [hit["filename"] for hit in body["items"]]
    assert filenames == ["hair_salon_notes.md", "car.txt"]
    assert "keyword" in body["items"][0]["matched_by"]
    assert body["items"][0]["score"] > body["items"][1]["score"]


async def test_search_finds_images_by_generated_tags(client: AsyncClient):
    await upload(client, "black_car.png", image_bytes("PNG"), "image/png")
    response = await client.get("/api/search", params={"q": "car"})
    assert [hit["filename"] for hit in response.json()["items"]] == ["black_car.png"]


async def test_search_finds_paperwork_images_by_the_document_category(client: AsyncClient):
    await upload(client, "receipt.png", image_bytes("PNG"), "image/png")
    await upload(client, "black_car.png", image_bytes("PNG", 24, 24), "image/png")
    response = await client.get("/api/search", params={"q": "document"})
    assert [hit["filename"] for hit in response.json()["items"]] == ["receipt.png"]


async def test_blank_search_is_rejected(client: AsyncClient):
    response = await client.get("/api/search", params={"q": "   "})
    assert response.status_code == 400
    assert response.json()["detail"]


async def test_hebrew_language_code_is_stored_with_the_text_index(client: AsyncClient):
    response = await upload(client, "hebrew_note.txt", HEBREW_NOTE)
    assert response.status_code == 201
    assert response.json()["status"] == "ready"
    assert response.json()["ai"]["lang_code"] == "he"


async def test_failed_insert_does_not_leave_the_stored_bytes_behind(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    async def failing_insert(self: AssetsRepository, document: dict) -> str:
        raise RuntimeError("database write failed")

    monkeypatch.setattr(AssetsRepository, "insert", failing_insert)
    with pytest.raises(RuntimeError, match="database write failed"):
        await upload(client, "hair_salon_notes.md", SALON_NOTES)

    mongo_client = AsyncMongoClient(MONGODB_TEST_URI)
    try:
        assert await mongo_client[TEST_DATABASE_NAME][GRIDFS_FILES_COLLECTION].count_documents({}) == 0
    finally:
        await mongo_client.close()


async def test_upload_errors_use_the_detail_shape(client: AsyncClient):
    unsupported = await upload(client, "drawing.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>")
    assert unsupported.status_code == 415
    assert unsupported.json()["detail"]
    empty = await upload(client, "empty.txt", b"")
    assert empty.status_code == 400
    too_large = await upload(client, "big.txt", b"a" * 30_000)
    assert too_large.status_code == 413
    assert "too big" in too_large.json()["detail"]
