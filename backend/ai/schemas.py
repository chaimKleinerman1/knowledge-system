from typing import Literal

from pydantic import BaseModel

AssetCategory = Literal["photo", "document", "screenshot", "diagram", "text_note", "other"]

MAX_TAGS = 15
MAX_KEYWORDS = 25
MAX_TEXT_CONTENT_CHARS = 4000


class AssetMetadata(BaseModel):
    """The JSON the model must return. Field names are part of the prompt contract."""

    description: str
    tags: list[str]
    keywords: list[str]
    text_content: str | None = None
    text_truncated: bool = False
    # Deliberately not called "language": MongoDB treats a field with that name as a
    # text-index language override and rejects values such as "he".
    lang_code: str | None = None
    category: AssetCategory


def normalise_metadata(metadata: AssetMetadata) -> AssetMetadata:
    text_content = _blank_to_none(metadata.text_content)
    text_truncated = metadata.text_truncated
    if text_content is not None and len(text_content) > MAX_TEXT_CONTENT_CHARS:
        text_content = text_content[:MAX_TEXT_CONTENT_CHARS]
        text_truncated = True
    return metadata.model_copy(
        update={
            "description": " ".join(metadata.description.split()),
            "tags": normalise_terms(metadata.tags, MAX_TAGS),
            "keywords": normalise_terms(metadata.keywords, MAX_KEYWORDS),
            "text_content": text_content,
            "text_truncated": text_truncated,
            "lang_code": _normalise_lang_code(metadata.lang_code),
        }
    )


def normalise_terms(terms: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        # The Mongo tokenizer does not split on underscores, so "id_card" would only
        # match a query for "id_card"; spaces make both words searchable.
        cleaned = " ".join(term.replace("_", " ").lower().split())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if len(result) == limit:
            break
    return result


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalise_lang_code(value: str | None) -> str | None:
    cleaned = _blank_to_none(value)
    return cleaned.lower() if cleaned else None
