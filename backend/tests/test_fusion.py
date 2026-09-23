import math

import pytest

from services.processing.fusion import cosine_similarity, reciprocal_rank_fusion


def test_cosine_of_identical_vectors_is_one():
    assert math.isclose(cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)


def test_cosine_ignores_magnitude():
    assert math.isclose(cosine_similarity([1.0, 0.0], [5.0, 0.0]), 1.0)


def test_cosine_of_orthogonal_vectors_is_zero():
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)


def test_cosine_of_opposite_vectors_is_minus_one():
    assert math.isclose(cosine_similarity([1.0, 1.0], [-1.0, -1.0]), -1.0)


def test_cosine_with_a_zero_vector_is_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_cosine_rejects_different_lengths():
    with pytest.raises(ValueError):
        cosine_similarity([1.0], [1.0, 2.0])


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


def test_reciprocal_rank_fusion_records_which_lists_matched():
    fused = {hit.id: hit.matched_by for hit in reciprocal_rank_fusion({"keyword": ["a", "b"], "semantic": ["b", "c"]})}
    assert fused == {"a": ["keyword"], "b": ["keyword", "semantic"], "c": ["semantic"]}


def test_reciprocal_rank_fusion_keeps_first_list_order_on_ties():
    fused = reciprocal_rank_fusion({"keyword": ["a", "b"], "semantic": ["b", "a"]})
    assert [hit.id for hit in fused] == ["a", "b"]


def test_reciprocal_rank_fusion_of_empty_lists_is_empty():
    assert reciprocal_rank_fusion({"keyword": [], "semantic": []}) == []
