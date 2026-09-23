from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from models.errors import (
    AssetNotFoundError,
    BlankQueryError,
    DomainError,
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

STATUS_CODES: dict[type[DomainError], int] = {
    EmptyFileError: 400,
    BlankQueryError: 400,
    AssetNotFoundError: 404,
    FileTooLargeError: 413,
    UnsupportedFileTypeError: 415,
}
FALLBACK_STATUS_CODE = 400


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
        status_code = STATUS_CODES.get(type(error), FALLBACK_STATUS_CODE)
        return JSONResponse(status_code=status_code, content={"detail": error.message})
