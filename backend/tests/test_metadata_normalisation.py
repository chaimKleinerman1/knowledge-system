from ai.schemas import (
    MAX_KEYWORDS,
    MAX_TAGS,
    MAX_TEXT_CONTENT_CHARS,
    AssetMetadata,
    normalise_metadata,
    normalise_terms,
)


def make_metadata(**overrides: object) -> AssetMetadata:
    fields: dict[str, object] = {
        "description": "A portrait.",
        "tags": ["Photo", "person"],
        "keywords": ["portrait"],
        "text_content": None,
        "lang_code": "en",
        "category": "photo",
    }
    return AssetMetadata(**{**fields, **overrides})


def test_terms_are_lowercased_and_stripped():
    assert normalise_terms(["  Black Hair ", "PHOTO"], limit=10) == ["black hair", "photo"]


def test_duplicates_and_empties_are_dropped():
    assert normalise_terms(["photo", "Photo", "", "   ", "photo "], limit=10) == ["photo"]


def test_underscores_become_spaces():
    assert normalise_terms(["id_card", "black__hair"], limit=10) == ["id card", "black hair"]


def test_lists_are_capped():
    metadata = normalise_metadata(
        make_metadata(tags=[f"tag{index}" for index in range(40)], keywords=[f"key{index}" for index in range(40)])
    )
    assert len(metadata.tags) == MAX_TAGS
    assert len(metadata.keywords) == MAX_KEYWORDS


def test_cap_counts_distinct_terms_only():
    assert normalise_terms(["a", "a", "b", "b", "c"], limit=2) == ["a", "b"]


def test_text_content_is_capped_and_flagged():
    metadata = normalise_metadata(make_metadata(text_content="z" * (MAX_TEXT_CONTENT_CHARS + 5)))
    assert len(metadata.text_content or "") == MAX_TEXT_CONTENT_CHARS
    assert metadata.text_truncated is True


def test_blank_text_content_becomes_none():
    assert normalise_metadata(make_metadata(text_content="   \n")).text_content is None


def test_language_code_is_lowercased_and_blank_becomes_none():
    assert normalise_metadata(make_metadata(lang_code=" HE ")).lang_code == "he"
    assert normalise_metadata(make_metadata(lang_code="")).lang_code is None


def test_description_whitespace_is_collapsed():
    assert normalise_metadata(make_metadata(description="  two\n\n lines  ")).description == "two lines"
