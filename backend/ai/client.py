import logging
from dataclasses import dataclass
from typing import Protocol

import litellm

from ai.prompts import build_messages
from ai.schemas import AssetMetadata, normalise_metadata
from config import Settings
from models.asset import AssetKind, TokenUsage
from models.errors import AiAnswerCutOffError

logger = logging.getLogger(__name__)

JSON_FENCE = "```"


@dataclass(frozen=True)
class DescribePayload:
    filename: str
    text: str | None = None
    text_truncated: bool = False
    image_data_uri: str | None = None


@dataclass(frozen=True)
class DescribeResult:
    metadata: AssetMetadata
    model: str
    usage: TokenUsage
    finish_reason: str | None


@dataclass(frozen=True)
class EmbedResult:
    text_vectors: list[list[float]]
    image_vector: list[float] | None
    model: str


class AiClient(Protocol):
    async def describe(self, kind: AssetKind, payload: DescribePayload) -> DescribeResult: ...

    async def embed(self, texts: list[str], image_data_uri: str | None = None) -> EmbedResult: ...


class LiteLlmAiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def describe(self, kind: AssetKind, payload: DescribePayload) -> DescribeResult:
        # Temperature is left at the provider default on purpose: Gemini 3 models
        # are documented to loop when it is lowered.
        fallback_models = [self._settings.LLM_FALLBACK_MODEL] if self._settings.LLM_FALLBACK_MODEL else None
        response = await litellm.acompletion(
            model=self._settings.LLM_MODEL,
            messages=build_messages(kind, payload.filename, payload.text, payload.image_data_uri),
            response_format=AssetMetadata,
            max_tokens=self._settings.LLM_MAX_OUTPUT_TOKENS,
            timeout=self._settings.LLM_TIMEOUT_SECONDS,
            num_retries=self._settings.LLM_MAX_RETRIES,
            retry_strategy="exponential_backoff_retry",
            fallbacks=fallback_models,
        )
        choice = response.choices[0]
        finish_reason = choice.finish_reason
        if finish_reason == "length":
            raise AiAnswerCutOffError()
        metadata = normalise_metadata(AssetMetadata.model_validate_json(strip_json_fence(choice.message.content or "")))
        usage = TokenUsage(
            input_tokens=getattr(response.usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(response.usage, "completion_tokens", 0) or 0,
        )
        return DescribeResult(
            metadata=metadata,
            model=response.model or self._settings.LLM_MODEL,
            usage=usage,
            finish_reason=finish_reason,
        )

    async def embed(self, texts: list[str], image_data_uri: str | None = None) -> EmbedResult:
        inputs: list[str] = [*texts]
        if image_data_uri is not None:
            inputs.append(image_data_uri)
        response = await litellm.aembedding(
            model=self._settings.EMBEDDING_MODEL,
            input=inputs,
            dimensions=self._settings.EMBEDDING_DIMENSIONS,
            timeout=self._settings.LLM_TIMEOUT_SECONDS,
            num_retries=self._settings.LLM_MAX_RETRIES,
        )
        vectors = [list(item["embedding"]) for item in sorted(response.data, key=lambda item: item["index"])]
        text_vectors = vectors[: len(texts)]
        if len(text_vectors) < len(texts):
            raise RuntimeError(f"Embedding provider returned {len(vectors)} vectors for {len(inputs)} inputs")
        image_vector = vectors[len(texts)] if image_data_uri is not None and len(vectors) > len(texts) else None
        if image_data_uri is not None and image_vector is None:
            logger.warning("Embedding provider returned no image vector; storing the text vector only")
        return EmbedResult(
            text_vectors=text_vectors, image_vector=image_vector, model=response.model or self._settings.EMBEDDING_MODEL
        )


def strip_json_fence(content: str) -> str:
    # Some models wrap JSON in a markdown code block even in JSON mode.
    stripped = content.strip()
    if not stripped.startswith(JSON_FENCE):
        return stripped
    lines = stripped.splitlines()
    body = lines[1:]
    if body and body[-1].strip() == JSON_FENCE:
        body = body[:-1]
    return "\n".join(body).strip()
