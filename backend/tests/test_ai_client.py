from types import SimpleNamespace

import litellm
import pytest

from ai.client import DescribePayload, LiteLlmAiClient
from models.errors import AiAnswerCutOffError
from tests.conftest import make_settings

MODEL_ANSWER = (
    '{"description": "A black car.", "tags": ["Photo", "black_car", "car"], "keywords": ["vehicle"],'
    ' "text_content": null, "text_truncated": false, "lang_code": "en", "category": "photo"}'
)


def fake_response(content: str, finish_reason: str = "stop") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=34),
        model="gemini-3.5-flash-lite",
    )


async def test_describe_passes_the_fallback_model_and_parses_the_answer(monkeypatch: pytest.MonkeyPatch):
    seen_kwargs: dict = {}

    async def fake_acompletion(**kwargs):
        seen_kwargs.update(kwargs)
        return fake_response(MODEL_ANSWER)

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)
    client = LiteLlmAiClient(make_settings(LLM_MODEL="gemini/main", LLM_FALLBACK_MODEL="gemini/backup"))

    result = await client.describe("text", DescribePayload(filename="car.txt", text="A black car."))

    assert seen_kwargs["model"] == "gemini/main"
    assert seen_kwargs["fallbacks"] == ["gemini/backup"]
    assert result.model == "gemini-3.5-flash-lite"
    assert result.metadata.tags == ["photo", "black car", "car"]
    assert result.usage.input_tokens == 12 and result.usage.output_tokens == 34


async def test_describe_reports_a_cut_off_answer(monkeypatch: pytest.MonkeyPatch):
    async def fake_acompletion(**kwargs):
        return fake_response('{"description": "cut', finish_reason="length")

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)
    client = LiteLlmAiClient(make_settings(LLM_FALLBACK_MODEL=""))

    with pytest.raises(AiAnswerCutOffError):
        await client.describe("text", DescribePayload(filename="note.txt", text="hello"))
