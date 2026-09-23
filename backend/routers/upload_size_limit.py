from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Makes uvicorn drop the socket after the 413, so a client cannot keep streaming a rejected body.
CLOSE_CONNECTION_HEADERS = {"Connection": "close"}


class UploadSizeLimitMiddleware:
    """Stops an oversize upload before Starlette parses the multipart body.

    FastAPI reads and spools the whole form before the endpoint runs, so the checks inside the
    endpoint only ever see bytes that were already received. This layer rejects a Content-Length
    above the limit up front and cuts a body off while it streams in. A body sent without
    Content-Length (chunked) skips the header check but not the byte counter.
    """

    def __init__(self, app: ASGIApp, *, path: str, max_body_bytes: int, message: str) -> None:
        self._app = app
        self._path = path
        self._max_body_bytes = max_body_bytes
        self._message = message

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self._is_upload_request(scope):
            await self._app(scope, receive, send)
            return
        content_length = Headers(scope=scope).get("content-length")
        if content_length is not None and content_length.isdigit() and int(content_length) > self._max_body_bytes:
            response = JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={"detail": self._message},
                headers=CLOSE_CONNECTION_HEADERS,
            )
            await response(scope, receive, send)
            return
        await self._app(scope, self._counting_receive(receive), send)

    def _is_upload_request(self, scope: Scope) -> bool:
        return scope["type"] == "http" and scope["method"] == "POST" and scope["path"] == self._path

    def _counting_receive(self, receive: Receive) -> Receive:
        received_bytes = 0

        async def counting_receive() -> Message:
            nonlocal received_bytes
            message = await receive()
            received_bytes += len(message.get("body", b""))
            if received_bytes > self._max_body_bytes:
                # Raised inside the form parser, before any response has started. FastAPI re-raises an
                # HTTPException unchanged, and its handler answers with the usual {"detail": ...} body.
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=self._message,
                    headers=CLOSE_CONNECTION_HEADERS,
                )
            return message

        return counting_receive
