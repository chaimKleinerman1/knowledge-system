from ai.schemas import MAX_KEYWORDS, MAX_TAGS, AssetMetadata, normalise_metadata, normalise_terms


def test_terms_are_lowercased_deduplicated_and_split_on_underscores():
    terms = ["  Black Hair ", "PHOTO", "photo", "", "id_card"]
    assert normalise_terms(terms, limit=10) == ["black hair", "photo", "id card"]


def test_tag_and_keyword_lists_are_capped():
    metadata = normalise_metadata(
        AssetMetadata(
            description="A portrait.",
            tags=[f"tag{index}" for index in range(40)],
            keywords=[f"key{index}" for index in range(40)],
            category="photo",
        )
    )
    assert len(metadata.tags) == MAX_TAGS
    assert len(metadata.keywords) == MAX_KEYWORDS
