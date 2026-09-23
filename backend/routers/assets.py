import re
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status

from models.asset import AssetListResponse, AssetResponse
from routers.dependencies import get_asset_service
from services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])

MAX_LIST_LIMIT = 200
DEFAULT_LIST_LIMIT = 50
# Anything outside printable ASCII is invalid in an HTTP header value, and uvicorn refuses to send it.
HEADER_UNSAFE_CHARACTERS = re.compile(r"[^\x20-\x7e]")

AssetServiceDependency = Annotated[AssetService, Depends(get_asset_service)]


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File()],
    service: AssetServiceDependency,
) -> AssetResponse:
    outcome = await service.upload(file, _content_length(request))
    if outcome.deduplicated:
        response.status_code = status.HTTP_200_OK
    return AssetResponse.from_asset(outcome.asset, deduplicated=outcome.deduplicated)


@router.get("", response_model=AssetListResponse)
async def list_assets(
    service: AssetServiceDependency,
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = DEFAULT_LIST_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AssetListResponse:
    items, total = await service.list(limit, offset)
    return AssetListResponse(items=[AssetResponse.from_asset(asset) for asset in items], total=total)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str, service: AssetServiceDependency) -> AssetResponse:
    asset = await service.get(asset_id, include_content=True)
    return AssetResponse.from_asset(asset, include_content=True)


@router.get("/{asset_id}/file")
async def get_asset_file(asset_id: str, service: AssetServiceDependency) -> Response:
    asset, content = await service.read_file(asset_id)
    return Response(
        content=content,
        media_type=asset.mime_type,
        headers={"Content-Disposition": _inline_disposition(asset.filename)},
    )


@router.post("/{asset_id}/reprocess", response_model=AssetResponse)
async def reprocess_asset(asset_id: str, service: AssetServiceDependency) -> AssetResponse:
    asset = await service.reprocess(asset_id)
    return AssetResponse.from_asset(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: str, service: AssetServiceDependency) -> Response:
    await service.delete(asset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _content_length(request: Request) -> int | None:
    header = request.headers.get("content-length")
    return int(header) if header is not None and header.isdigit() else None


def _inline_disposition(filename: str) -> str:
    # Browsers need an ASCII fallback plus the RFC 5987 form for non-ASCII names.
    ascii_name = HEADER_UNSAFE_CHARACTERS.sub("?", filename).replace('"', "").replace("\\", "")
    return f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
