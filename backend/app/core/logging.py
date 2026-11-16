"""JSON logging with a request ID per request (docs/OBSERVABILITY.md §1, CODE_STYLE.md §9).

Never log request bodies, tokens or clinical values (docs/SECURITY.md §9).
"""

import json
import logging
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from datetime import UTC, datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.common.responses import error_body

LOGGER_NAME = "alovia"
REQUEST_ID_HEADER = "X-Request-ID"
EXTRA_FIELDS = ("method", "path", "status", "duration_ms")

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
logger = logging.getLogger(LOGGER_NAME)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        entry.update({k: getattr(record, k) for k in EXTRA_FIELDS if hasattr(record, k)})
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False


async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Give each request an ID, log one line for it, and turn crashes into INTERNAL_ERROR."""
    request_id = uuid.uuid4().hex
    request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled error")
        response = JSONResponse(
            error_body("INTERNAL_ERROR", "Something went wrong."), status_code=500
        )
    route = request.scope.get("route")
    # log the route template, not the raw path, so codes or IDs in the URL are not logged
    path = getattr(route, "path", request.url.path)
    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        },
    )
    return response
