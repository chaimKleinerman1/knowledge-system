from dataclasses import dataclass

from fastapi import Request
from pymongo.asynchronous.database import AsyncDatabase

from config import Settings
from services.asset_service import AssetService
from services.search_service import SearchService


@dataclass(frozen=True)
class AppContainer:
    """Everything a request handler may need, built once at startup."""

    settings: Settings
    database: AsyncDatabase
    asset_service: AssetService
    search_service: SearchService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_settings(request: Request) -> Settings:
    return get_container(request).settings


def get_database(request: Request) -> AsyncDatabase:
    return get_container(request).database


def get_asset_service(request: Request) -> AssetService:
    return get_container(request).asset_service


def get_search_service(request: Request) -> SearchService:
    return get_container(request).search_service
