import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

RRF_K = 60


@dataclass(frozen=True)
class FusedHit:
    id: str
    score: float
    matched_by: list[str]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"Vectors differ in length: {len(a)} and {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def reciprocal_rank_fusion(ranked_lists: Mapping[str, Sequence[str]], k: int = RRF_K) -> list[FusedHit]:
    """Merge ranked id lists: each list contributes 1 / (k + rank) to an id's score.

    Ties keep the order in which ids were first seen, so the first list's order wins.
    """
    scores: dict[str, float] = {}
    matched_by: dict[str, list[str]] = {}
    for list_name, ids in ranked_lists.items():
        for rank, item_id in enumerate(ids, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            matched_by.setdefault(item_id, []).append(list_name)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [FusedHit(id=item_id, score=score, matched_by=matched_by[item_id]) for item_id, score in ordered]
