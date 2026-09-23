import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ai.client import AiClient, LiteLlmAiClient
from config import Settings
from database.assets_repository import AssetsRepository
from database.files_repository import FilesRepository
from database.indexes import ensure_indexes
from database.mongo import create_mongo_client, get_database
from routers import assets, health, search
from routers.dependencies import AppContainer
from routers.error_handlers import register_error_handlers
from services.asset_service import AssetService
from services.search_service import SearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIRECTORY = Path(__file__).parent / "static"
API_PREFIX = "/api"


def create_app(settings: Settings | None = None, ai_client: AiClient | None = None) -> FastAPI:
    """Builds the app; tests pass their own settings and a fake AI client."""
    app_settings = settings or Settings()
    app_ai_client = ai_client or LiteLlmAiClient(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        mongo_client = create_mongo_client(app_settings.MONGODB_URI)
        database = get_database(mongo_client, app_settings.MONGODB_DB_NAME)
        try:
            await ensure_indexes(database)
        except Exception:
            # Keep serving so /api/health can report the database problem.
            logger.exception("Could not reach MongoDB at startup")
        ai_semaphore = asyncio.Semaphore(app_settings.AI_CONCURRENCY)
        assets_repository = AssetsRepository(database)
        app.state.container = AppContainer(
            settings=app_settings,
            database=database,
            asset_service=AssetService(
                app_settings, assets_repository, FilesRepository(database), app_ai_client, ai_semaphore
            ),
            search_service=SearchService(app_settings, assets_repository, app_ai_client, ai_semaphore),
        )
        yield
        await mongo_client.close()

    app = FastAPI(title="Knowledge Base API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(assets.router, prefix=API_PREFIX)
    app.include_router(search.router, prefix=API_PREFIX)
    mount_frontend(app, STATIC_DIRECTORY)
    return app


def mount_frontend(app: FastAPI, static_directory: Path) -> None:
    """Serve the built single-page app when it exists; API routes are registered first and win."""
    index_file = static_directory / "index.html"
    if not index_file.is_file():
        return
    assets_directory = static_directory / "assets"
    if assets_directory.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_directory), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_single_page_app(full_path: str) -> FileResponse:
        if full_path == API_PREFIX.strip("/") or full_path.startswith(API_PREFIX.strip("/") + "/"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        candidate = (static_directory / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(static_directory.resolve()):
            return FileResponse(candidate)
        return FileResponse(index_file)


# The app is built on demand (`uvicorn main:create_app --factory`), not at import time, so importing
# this module never needs a .env: the tests build their own app with test settings.
if __name__ == "__main__":
    uvicorn.run("main:create_app", factory=True, host="0.0.0.0", port=Settings().PORT, reload=True)
