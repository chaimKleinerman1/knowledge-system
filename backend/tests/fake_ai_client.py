import hashlib
import math
import re

from ai.client import DescribePayload, DescribeResult, EmbedResult
from ai.schemas import AssetMetadata, normalise_metadata
from models.asset import AssetKind, TokenUsage

FAKE_MODEL = "fake/describe-v1"
FAKE_EMBEDDING_MODEL = "fake/embed-v1"
DESCRIPTION_CHARS = 200
MAX_FAKE_TAGS = 10
MAX_FAKE_KEYWORDS = 20
MIN_WORD_LENGTH = 3
HEBREW_LETTERS = re.compile(r"[֐-׿]")
DOCUMENT_WORDS = frozenset(
    {"receipt", "invoice", "card", "passport", "form", "contract", "scan", "document", "letter", "statement", "bill"}
)
WORDS = re.compile(r"[^\W_]+", re.UNICODE)


class FakeAiClient:
    """Deterministic stand-in for the model: metadata comes from the filename and text.

    Search tests can predict the outcome because the same input always yields the same
    tags, keywords and vectors. Vectors are hashed bags of words, so files that share
    words are close in cosine space.
    """

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions
        # Tests flip this to simulate an outage and check the failed -> reprocess path.
        self.fail_describe = False

    async def describe(self, kind: AssetKind, payload: DescribePayload) -> DescribeResult:
        if self.fail_describe:
            raise RuntimeError("Fake AI outage")
        metadata = _describe_text(payload) if kind == "text" else _describe_image(payload)
        return DescribeResult(
            metadata=normalise_metadata(metadata),
            model=FAKE_MODEL,
            usage=TokenUsage(input_tokens=len(payload.text or ""), output_tokens=len(metadata.description)),
            finish_reason="stop",
        )

    async def embed(self, texts: list[str], image_data_uri: str | None = None) -> EmbedResult:
        text_vectors = [self._vector_for(text) for text in texts]
        image_vector = self._one_hot_vector(image_data_uri) if image_data_uri is not None else None
        return EmbedResult(text_vectors=text_vectors, image_vector=image_vector, model=FAKE_EMBEDDING_MODEL)

    def _one_hot_vector(self, seed: str) -> list[float]:
        # A data URI has no words worth hashing; one stable dimension per distinct image is enough.
        vector = [0.0] * self.dimensions
        vector[int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:4], "big") % self.dimensions] = 1.0
        return vector

    def _vector_for(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in _words(text):
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            vector[0] = 1.0
            return vector
        return [value / norm for value in vector]


def _describe_text(payload: DescribePayload) -> AssetMetadata:
    text = payload.text or ""
    words = _distinct_words(text)
    # Like the real prompt: only paperwork gets the "document" tag, plain notes do not.
    generic_tags = ["text note", "document"] if any(word in DOCUMENT_WORDS for word in words) else ["text note"]
    return AssetMetadata(
        description=" ".join(text.split())[:DESCRIPTION_CHARS] or f"Text file named {payload.filename}",
        tags=[*generic_tags, *words[:MAX_FAKE_TAGS]],
        keywords=words[:MAX_FAKE_KEYWORDS],
        text_content=None,
        text_truncated=payload.text_truncated,
        lang_code="he" if HEBREW_LETTERS.search(text) else "en",
        category="text_note",
    )


def _describe_image(payload: DescribePayload) -> AssetMetadata:
    stem_words = _distinct_words(_filename_stem(payload.filename))
    # The real prompt tags every picture of paperwork as a "document"; the fake mirrors that rule
    # from the filename so search tests behave like the live model would.
    is_document = any(word in DOCUMENT_WORDS for word in stem_words)
    category = "document" if is_document else "photo"
    return AssetMetadata(
        description=f"Image named {payload.filename} showing {' '.join(stem_words) or 'an unknown subject'}.",
        tags=[category, "image", *stem_words[:MAX_FAKE_TAGS]],
        keywords=stem_words[:MAX_FAKE_KEYWORDS],
        text_content=None,
        text_truncated=False,
        lang_code=None,
        category=category,
    )


def _filename_stem(filename: str) -> str:
    return filename.rsplit(".", 1)[0] if "." in filename else filename


def _words(text: str) -> list[str]:
    return [word.lower() for word in WORDS.findall(text)]


def _distinct_words(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for word in _words(text):
        if len(word) < MIN_WORD_LENGTH or word in seen:
            continue
        seen.add(word)
        result.append(word)
    return result
