from typing import Annotated

from fastapi import APIRouter, Depends, Query

from config import Settings
from models.asset import AssetResponse, SearchHit, SearchResponse
from routers.dependencies import get_search_service, get_settings
from services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])

MAX_SEARCH_LIMIT = 50


@router.get("", response_model=SearchResponse)
async def search(
    service: Annotated[SearchService, Depends(get_search_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    q: str = "",
    limit: Annotated[int | None, Query(ge=1, le=MAX_SEARCH_LIMIT)] = None,
) -> SearchResponse:
    results = await service.search(q, limit or settings.SEARCH_LIMIT)
    hits = [
        SearchHit(
            **AssetResponse.from_asset(result.asset).model_dump(), matched_by=result.matched_by, score=result.score
        )
        for result in results
    ]
    return SearchResponse(query=" ".join(q.split()), items=hits)
