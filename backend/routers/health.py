from typing import Annotated

from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from database.mongo import is_database_reachable
from models.asset import HealthResponse
from routers.dependencies import get_database

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(database: Annotated[AsyncDatabase, Depends(get_database)]) -> HealthResponse:
    reachable = await is_database_reachable(database)
    return HealthResponse(status="ok", database="ok" if reachable else "error")
