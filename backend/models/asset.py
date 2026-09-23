from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AssetKind = Literal["image", "text"]
AssetStatus = Literal["processing", "ready", "failed"]
MatchSource = Literal["keyword", "semantic"]


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class AiMetadata(BaseModel):
    description: str
    tags: list[str]
    keywords: list[str]
    category: str
    lang_code: str | None = None
    text_content: str | None = None
    text_truncated: bool = False
    model: str
    prompt_version: str
    processed_at: datetime
    usage: TokenUsage = Field(default_factory=TokenUsage)


class Asset(BaseModel):
    """The stored asset as the rest of the backend sees it (no Mongo types)."""

    id: str
    filename: str
    kind: AssetKind
    mime_type: str
    size_bytes: int
    sha256: str
    gridfs_id: str
    status: AssetStatus
    error: str | None = None
    extracted_text: str | None = None
    ai: AiMetadata | None = None
    embedding_text: list[float] | None = None
    embedding_image: list[float] | None = None
    embedding_model: str | None = None
    created_at: datetime
    updated_at: datetime


class AiMetadataResponse(BaseModel):
    description: str
    tags: list[str]
    keywords: list[str]
    category: str
    lang_code: str | None
    text_content: str | None
    text_truncated: bool
    model: str
    prompt_version: str
    processed_at: datetime

    @classmethod
    def from_metadata(cls, metadata: AiMetadata, *, include_content: bool) -> "AiMetadataResponse":
        return cls(
            description=metadata.description,
            tags=metadata.tags,
            keywords=metadata.keywords,
            category=metadata.category,
            lang_code=metadata.lang_code,
            text_content=metadata.text_content if include_content else None,
            text_truncated=metadata.text_truncated,
            model=metadata.model,
            prompt_version=metadata.prompt_version,
            processed_at=metadata.processed_at,
        )


class AssetResponse(BaseModel):
    id: str
    filename: str
    kind: AssetKind
    mime_type: str
    size_bytes: int
    status: AssetStatus
    error: str | None
    created_at: datetime
    updated_at: datetime
    file_url: str
    ai: AiMetadataResponse | None
    extracted_text: str | None
    deduplicated: bool = False

    @classmethod
    def from_asset(cls, asset: Asset, *, include_content: bool = False, deduplicated: bool = False) -> "AssetResponse":
        return cls(
            id=asset.id,
            filename=asset.filename,
            kind=asset.kind,
            mime_type=asset.mime_type,
            size_bytes=asset.size_bytes,
            status=asset.status,
            error=asset.error,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            file_url=file_url_for(asset.id),
            ai=AiMetadataResponse.from_metadata(asset.ai, include_content=include_content) if asset.ai else None,
            extracted_text=asset.extracted_text if include_content else None,
            deduplicated=deduplicated,
        )


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int


class SearchHit(AssetResponse):
    matched_by: list[MatchSource]
    score: float


class SearchResponse(BaseModel):
    query: str
    items: list[SearchHit]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok", "error"]


def file_url_for(asset_id: str) -> str:
    return f"/api/assets/{asset_id}/file"
