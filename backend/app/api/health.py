"""GET /api/v1/health (docs/API.md §4.1, docs/OBSERVABILITY.md §2)."""

from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.api import API_PREFIX
from app.common.responses import ok
from app.core.logging import logger

router = APIRouter(prefix=API_PREFIX)


@router.get("/health")
def health(request: Request) -> dict[str, Any]:
    # models_loaded and rules_loaded turn true in the ML-move and rule-file tasks
    return ok(
        {
            "status": "ok",
            "db": _db_status(request.app.state.engine),
            "models_loaded": False,
            "rules_loaded": {"genetic": False, "symptoms": False, "journey": False},
            "version": __version__,
        }
    )


def _db_status(engine: Engine) -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("database check failed", extra={"reason": type(exc).__name__})
        return "error"
    return "ok"
