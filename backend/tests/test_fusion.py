import math

from services.processing.fusion import cosine_similarity, reciprocal_rank_fusion


def test_cosine_similarity_measures_direction_not_magnitude():
    assert math.isclose(cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)
    assert math.isclose(cosine_similarity([1.0, 0.0], [5.0, 0.0]), 1.0)
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)


def test_reciprocal_rank_fusion_worked_example():
    # Keyword list: portrait 1st, black car 2nd, salon notes 3rd.
    # Semantic list: dark hair 1st, portrait 2nd, salon notes 3rd.
    fused = reciprocal_rank_fusion(
        {
            "keyword": ["portrait", "black car", "salon notes"],
            "semantic": ["dark hair", "portrait", "salon notes"],
        }
    )
    assert [hit.id for hit in fused] == ["portrait", "salon notes", "dark hair", "black car"]
    assert math.isclose(fused[0].score, 1 / 61 + 1 / 62)
    assert math.isclose(fused[1].score, 2 / 63)
    assert math.isclose(fused[2].score, 1 / 61)
    assert math.isclose(fused[3].score, 1 / 62)
    assert fused[0].matched_by == ["keyword", "semantic"]
    assert fused[3].matched_by == ["keyword"]
