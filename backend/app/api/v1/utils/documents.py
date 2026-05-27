from __future__ import annotations

from datetime import date, datetime
from typing import Any


def public_doc(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in document.items():
        if key == "_id":
            continue
        cleaned[key] = serialize_value(value)
    return cleaned


def serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serialize_value(item) for key, item in value.items() if key != "_id"}
    return value


def clean_update(update: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in update.items() if value is not None and key != "id"}
