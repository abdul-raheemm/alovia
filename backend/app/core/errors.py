"""Typed application errors and the handlers that turn them into the API envelope.

Codes and HTTP statuses: docs/API.md §3. Unexpected exceptions are caught in
app.core.logging.request_context so they are logged with the request ID.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.responses import error_body

# HTTP status → error code, for errors raised by the framework itself (docs/API.md §3)
STATUS_CODES = {
    400: "VALIDATION_ERROR",
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "FILE_TOO_LARGE",
    415: "UNSUPPORTED_FILE_TYPE",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}


class AppError(Exception):
    """Raised by services; the handler sends it as the error envelope."""

    def __init__(
        self, code: str, message: str, status: int = 400, fields: dict[str, str] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.fields = fields


async def _app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse(error_body(exc.code, exc.message, exc.fields), status_code=exc.status)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields = {
        ".".join(str(part) for part in err["loc"][1:]) or str(err["loc"][0]): err["msg"]
        for err in exc.errors()
    }
    return JSONResponse(error_body("VALIDATION_ERROR", "Invalid input.", fields), status_code=400)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    # a status outside API.md §3 keeps its HTTP status and uses VALIDATION_ERROR
    code = STATUS_CODES.get(exc.status_code, "VALIDATION_ERROR")
    return JSONResponse(
        error_body(code, str(exc.detail)), status_code=exc.status_code, headers=exc.headers
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
