import asyncio
import logging
from dataclasses import dataclass

from ai.client import AiClient
from config import Settings
from database.assets_repository import AssetsRepository, StoredEmbeddings
from models.asset import Asset
from models.errors import BlankQueryError
from services.processing.fusion import cosine_similarity, reciprocal_rank_fusion

logger = logging.getLogger(__name__)

KEYWORD_LIST = "keyword"
SEMANTIC_LIST = "semantic"
PASS_LIMIT = 20


@dataclass(frozen=True)
class SearchResult:
    asset: Asset
    matched_by: list[str]
    score: float


class SearchService:
    def __init__(
        self,
        settings: Settings,
        assets_repository: AssetsRepository,
        ai_client: AiClient,
        ai_semaphore: asyncio.Semaphore,
    ) -> None:
        self._settings = settings
        self._assets = assets_repository
        self._ai_client = ai_client
        self._ai_semaphore = ai_semaphore

    async def search(self, query: str, limit: int) -> list[SearchResult]:
        cleaned_query = " ".join(query.split())
        if not cleaned_query:
            raise BlankQueryError("Type something to search for.")

        keyword_assets = await self._keyword_pass(cleaned_query)
        semantic_ids = await self._semantic_pass(cleaned_query)
        fused = reciprocal_rank_fusion({KEYWORD_LIST: list(keyword_assets), SEMANTIC_LIST: semantic_ids})[:limit]

        missing_ids = [hit.id for hit in fused if hit.id not in keyword_assets]
        assets = {**keyword_assets, **(await self._assets.find_many_by_ids(missing_ids) if missing_ids else {})}
        return [
            SearchResult(asset=assets[hit.id], matched_by=hit.matched_by, score=hit.score)
            for hit in fused
            if hit.id in assets
        ]

    async def _keyword_pass(self, query: str) -> dict[str, Asset]:
        # MongoDB ORs bare words, so a plain "black hair" would also match a black car. The exact
        # phrase goes first; the second pass quotes every word, which makes each of them required.
        cleaned = query.replace(chr(34), " ")
        phrase_query = f'"{cleaned}"'
        all_words_query = " ".join(f'"{word}"' for word in cleaned.split())
        ordered: dict[str, Asset] = {}
        for text_query in (phrase_query, all_words_query):
            for asset in await self._assets.search_text(text_query, PASS_LIMIT):
                ordered.setdefault(asset.id, asset)
        return ordered

    async def _semantic_pass(self, query: str) -> list[str]:
        try:
            async with self._ai_semaphore:
                embedded = await self._ai_client.embed([query])
        except Exception:
            logger.warning("Query embedding failed; returning keyword results only", exc_info=True)
            return []
        query_vector = embedded.text_vectors[0]
        scored = [
            (record.asset_id, score)
            for record in await self._assets.find_ready_embeddings()
            if (score := _best_similarity(query_vector, record)) >= self._settings.SEMANTIC_MIN_SCORE
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [asset_id for asset_id, _ in scored[:PASS_LIMIT]]


def _best_similarity(query_vector: list[float], record: StoredEmbeddings) -> float:
    similarities = [
        cosine_similarity(query_vector, vector)
        for vector in (record.text_vector, record.image_vector)
        if vector is not None and len(vector) == len(query_vector)
    ]
    return max(similarities, default=-1.0)
