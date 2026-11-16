"""Response envelope (docs/API.md §2): every response is {"data": ..., "error": ...}."""

from typing import Any


def ok(data: Any) -> dict[str, Any]:
    return {"data": data, "error": None}


def error_body(code: str, message: str, fields: dict[str, str] | None = None) -> dict[str, Any]:
    return {"data": None, "error": {"code": code, "message": message, "fields": fields}}
