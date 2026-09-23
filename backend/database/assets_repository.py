from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from database.indexes import ASSETS_COLLECTION
from models.asset import AiMetadata, Asset

# Lists and search results never carry the heavy fields.
LIGHT_PROJECTION = {"extracted_text": 0, "ai.text_content": 0, "embedding_text": 0, "embedding_image": 0}
EMBEDDINGS_PROJECTION = {"embedding_text": 1, "embedding_image": 1}
TEXT_SCORE_SORT = [("score", {"$meta": "textScore"})]


@dataclass(frozen=True)
class StoredEmbeddings:
    asset_id: str
    text_vector: list[float] | None
    image_vector: list[float] | None


class AssetsRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database[ASSETS_COLLECTION]

    async def insert(self, document: dict[str, Any]) -> str:
        now = utc_now()
        stored = {**document, "gridfs_id": ObjectId(document["gridfs_id"]), "created_at": now, "updated_at": now}
        result = await self._collection.insert_one(stored)
        return str(result.inserted_id)

    async def find_by_id(self, asset_id: str, *, include_content: bool = False) -> Asset | None:
        if not ObjectId.is_valid(asset_id):
            return None
        projection = None if include_content else LIGHT_PROJECTION
        document = await self._collection.find_one({"_id": ObjectId(asset_id)}, projection)
        return to_asset(document) if document else None

    async def find_by_sha256(self, sha256: str) -> Asset | None:
        document = await self._collection.find_one({"sha256": sha256}, LIGHT_PROJECTION)
        return to_asset(document) if document else None

    async def find_many_by_ids(self, asset_ids: list[str]) -> dict[str, Asset]:
        object_ids = [ObjectId(asset_id) for asset_id in asset_ids if ObjectId.is_valid(asset_id)]
        cursor = self._collection.find({"_id": {"$in": object_ids}}, LIGHT_PROJECTION)
        return {str(document["_id"]): to_asset(document) async for document in cursor}

    async def list_newest(self, limit: int, offset: int) -> tuple[list[Asset], int]:
        cursor = (
            self._collection.find({}, LIGHT_PROJECTION)
            .sort([("created_at", DESCENDING), ("_id", DESCENDING)])
            .skip(offset)
            .limit(limit)
        )
        items = [to_asset(document) async for document in cursor]
        total = await self._collection.count_documents({})
        return items, total

    async def update(self, asset_id: str, fields: dict[str, Any]) -> None:
        await self._collection.update_one({"_id": ObjectId(asset_id)}, {"$set": {**fields, "updated_at": utc_now()}})

    async def delete(self, asset_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(asset_id)})
        return result.deleted_count == 1

    async def search_text(self, query: str, limit: int) -> list[Asset]:
        cursor = (
            self._collection.find({"$text": {"$search": query}}, LIGHT_PROJECTION).sort(TEXT_SCORE_SORT).limit(limit)
        )
        return [to_asset(document) async for document in cursor]

    async def find_ready_embeddings(self) -> list[StoredEmbeddings]:
        cursor = self._collection.find({"status": "ready"}, EMBEDDINGS_PROJECTION).sort("_id", ASCENDING)
        return [
            StoredEmbeddings(
                asset_id=str(document["_id"]),
                text_vector=document.get("embedding_text"),
                image_vector=document.get("embedding_image"),
            )
            async for document in cursor
        ]


def to_asset(document: dict[str, Any]) -> Asset:
    ai_document = document.get("ai")
    return Asset(
        id=str(document["_id"]),
        filename=document["filename"],
        kind=document["kind"],
        mime_type=document["mime_type"],
        size_bytes=document["size_bytes"],
        sha256=document["sha256"],
        gridfs_id=str(document["gridfs_id"]),
        status=document["status"],
        error=document.get("error"),
        extracted_text=document.get("extracted_text"),
        ai=AiMetadata.model_validate(ai_document) if ai_document else None,
        embedding_text=document.get("embedding_text"),
        embedding_image=document.get("embedding_image"),
        embedding_model=document.get("embedding_model"),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


def utc_now() -> datetime:
    return datetime.now(UTC)
