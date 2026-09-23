import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from pymongo.errors import DuplicateKeyError

from ai.client import AiClient, DescribePayload
from ai.prompts import PROMPT_VERSION
from ai.schemas import AssetMetadata
from config import Settings
from database.assets_repository import AssetsRepository, utc_now
from database.files_repository import FilesRepository
from models.asset import Asset, AssetKind
from models.errors import AiAnswerCutOffError, AssetNotFoundError
from services.processing.preparation import cap_stored_text, prepare_image, prepare_text
from services.processing.validation import ByteStream, validate_upload

logger = logging.getLogger(__name__)

GENERIC_AI_FAILURE_MESSAGE = "The AI could not analyze this file. Use Retry analysis to try again."
ASSET_NOT_FOUND_MESSAGE = "This file does not exist or was deleted."
METADATA_TEXT_CONTENT_CHARS = 2000


@dataclass(frozen=True)
class UploadOutcome:
    asset: Asset
    deduplicated: bool


@dataclass(frozen=True)
class PreparedInput:
    payload: DescribePayload
    extracted_text: str | None


class AssetService:
    """Runs the upload pipeline: validate -> store -> describe -> embed -> persist."""

    def __init__(
        self,
        settings: Settings,
        assets_repository: AssetsRepository,
        files_repository: FilesRepository,
        ai_client: AiClient,
        ai_semaphore: asyncio.Semaphore,
    ) -> None:
        self._settings = settings
        self._assets = assets_repository
        self._files = files_repository
        self._ai_client = ai_client
        self._ai_semaphore = ai_semaphore

    async def upload(self, filename: str | None, content_length: int | None, stream: ByteStream) -> UploadOutcome:
        validated = await validate_upload(filename, content_length, stream, self._settings)
        existing = await self._assets.find_by_sha256(validated.sha256)
        if existing is not None:
            return await self._deduplicated(existing)

        prepared = self._prepare(validated.kind, validated.content, validated.filename)
        gridfs_id = await self._files.upload(validated.filename, validated.content, validated.mime_type)
        document: dict[str, Any] = {
            "filename": validated.filename,
            "kind": validated.kind,
            "mime_type": validated.mime_type,
            "size_bytes": validated.size_bytes,
            "sha256": validated.sha256,
            "gridfs_id": gridfs_id,
            "status": "processing",
            "error": None,
            "extracted_text": prepared.extracted_text,
            "ai": None,
            "embedding_text": None,
            "embedding_image": None,
            "embedding_model": None,
        }
        try:
            asset_id = await self._assets.insert(document)
        except DuplicateKeyError:
            # Two uploads of the same bytes raced; the first one owns the record.
            await self._files.delete(gridfs_id)
            winner = await self._assets.find_by_sha256(validated.sha256)
            if winner is None:
                raise
            return await self._deduplicated(winner)
        except Exception:
            # Without a document nothing would ever reference, or delete, the stored bytes.
            await self._files.delete(gridfs_id)
            raise

        asset = await self._analyze(asset_id, validated.kind, prepared.payload)
        return UploadOutcome(asset=asset, deduplicated=False)

    async def reprocess(self, asset_id: str) -> Asset:
        asset = await self.get(asset_id)
        content = await self._files.download(asset.gridfs_id)
        if content is None:
            raise AssetNotFoundError(ASSET_NOT_FOUND_MESSAGE)
        prepared = self._prepare(asset.kind, content, asset.filename)
        await self._assets.update(asset_id, {"status": "processing", "error": None})
        return await self._analyze(asset_id, asset.kind, prepared.payload)

    async def get(self, asset_id: str, *, include_content: bool = False) -> Asset:
        asset = await self._assets.find_by_id(asset_id, include_content=include_content)
        if asset is None:
            raise AssetNotFoundError(ASSET_NOT_FOUND_MESSAGE)
        return asset

    async def list(self, limit: int, offset: int) -> tuple[list[Asset], int]:
        return await self._assets.list_newest(limit, offset)

    async def read_file(self, asset_id: str) -> tuple[Asset, bytes]:
        asset = await self.get(asset_id)
        content = await self._files.download(asset.gridfs_id)
        if content is None:
            raise AssetNotFoundError(ASSET_NOT_FOUND_MESSAGE)
        return asset, content

    async def delete(self, asset_id: str) -> None:
        asset = await self.get(asset_id)
        await self._files.delete(asset.gridfs_id)
        await self._assets.delete(asset_id)

    async def _deduplicated(self, existing: Asset) -> UploadOutcome:
        asset = await self.reprocess(existing.id) if existing.status == "failed" else existing
        return UploadOutcome(asset=asset, deduplicated=True)

    def _prepare(self, kind: AssetKind, content: bytes, filename: str) -> PreparedInput:
        if kind == "image":
            return PreparedInput(
                payload=DescribePayload(filename=filename, image_data_uri=prepare_image(content)), extracted_text=None
            )
        text = content.decode("utf-8")
        prepared_text = prepare_text(text, self._settings.LLM_TEXT_INPUT_CHARS)
        payload = DescribePayload(filename=filename, text=prepared_text.text, text_truncated=prepared_text.truncated)
        return PreparedInput(payload=payload, extracted_text=cap_stored_text(text))

    async def _analyze(self, asset_id: str, kind: AssetKind, payload: DescribePayload) -> Asset:
        try:
            update = await self._describe_and_embed(kind, payload)
        except AiAnswerCutOffError as error:
            logger.warning("AI answer cut off for asset %s", asset_id)
            update = _failed_update(error.message)
        except Exception:
            logger.exception("AI processing failed for asset %s", asset_id)
            update = _failed_update(GENERIC_AI_FAILURE_MESSAGE)
        await self._assets.update(asset_id, update)
        return await self.get(asset_id)

    async def _describe_and_embed(self, kind: AssetKind, payload: DescribePayload) -> dict[str, Any]:
        async with self._ai_semaphore:
            described = await self._ai_client.describe(kind, payload)
        metadata_text = build_metadata_text(described.metadata)
        async with self._ai_semaphore:
            embedded = await self._ai_client.embed([metadata_text], payload.image_data_uri)
        return {
            "ai": {
                **described.metadata.model_dump(),
                "model": described.model,
                "prompt_version": PROMPT_VERSION,
                "processed_at": utc_now(),
                "usage": described.usage.model_dump(),
            },
            "embedding_text": embedded.text_vectors[0],
            "embedding_image": embedded.image_vector,
            "embedding_model": embedded.model,
            "status": "ready",
            "error": None,
        }


def build_metadata_text(metadata: AssetMetadata) -> str:
    parts = [metadata.description, " ".join(metadata.tags), " ".join(metadata.keywords)]
    if metadata.text_content:
        parts.append(metadata.text_content[:METADATA_TEXT_CONTENT_CHARS])
    return "\n".join(part for part in parts if part)


def _failed_update(message: str) -> dict[str, Any]:
    return {"status": "failed", "error": message}
