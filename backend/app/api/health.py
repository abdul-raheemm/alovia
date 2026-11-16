"""GET /api/v1/health (docs/API.md §4.1, docs/OBSERVABILITY.md §2)."""

from typing import Any

from fastapi import APIRouter

from app import __version__
from app.api import API_PREFIX
from app.common.responses import ok

router = APIRouter(prefix=API_PREFIX)


@router.get("/health")
def health() -> dict[str, Any]:
    # Nothing is loaded yet: the ML-move task sets models_loaded, the rule-file tasks set
    # rules_loaded, and the database task adds "db" (no placeholder "ok" until it is checked).
    return ok(
        {
            "status": "ok",
            "models_loaded": False,
            "rules_loaded": {"genetic": False, "symptoms": False, "journey": False},
            "version": __version__,
        }
    )
