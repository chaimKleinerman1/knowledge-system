from pymongo.asynchronous.database import AsyncDatabase

ASSETS_COLLECTION = "assets"
TEXT_INDEX_NAME = "assets_text"
SHA256_INDEX_NAME = "sha256_unique"
STATUS_INDEX_NAME = "status"

TEXT_INDEX_WEIGHTS = {
    "ai.tags": 10,
    "ai.category": 8,
    "ai.keywords": 8,
    "ai.description": 5,
    "ai.text_content": 4,
    "filename": 3,
    "extracted_text": 2,
}
# Without this override MongoDB reads any field named "language" as the document's
# text-index language and rejects inserts holding values such as "he" (error 17262).
LANGUAGE_OVERRIDE_FIELD = "__no_lang__"


async def ensure_indexes(database: AsyncDatabase) -> None:
    assets = database[ASSETS_COLLECTION]
    await assets.create_index(
        [(field, "text") for field in TEXT_INDEX_WEIGHTS],
        weights=TEXT_INDEX_WEIGHTS,
        default_language="english",
        language_override=LANGUAGE_OVERRIDE_FIELD,
        name=TEXT_INDEX_NAME,
    )
    await assets.create_index("sha256", unique=True, name=SHA256_INDEX_NAME)
    await assets.create_index("status", name=STATUS_INDEX_NAME)
