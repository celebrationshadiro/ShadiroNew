import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
request_path_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_path", default=None)
user_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)
execution_ms_ctx: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar("execution_ms", default=None)


def set_request_context(
    *,
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    user_id: Optional[str] = None,
    execution_ms: Optional[float] = None,
) -> None:
    if request_id is not None:
        request_id_ctx.set(request_id)
    if path is not None:
        request_path_ctx.set(path)
    if user_id is not None:
        user_id_ctx.set(user_id)
    if execution_ms is not None:
        execution_ms_ctx.set(execution_ms)


def clear_request_context() -> None:
    request_id_ctx.set(None)
    request_path_ctx.set(None)
    user_id_ctx.set(None)
    execution_ms_ctx.set(None)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "path": request_path_ctx.get(),
            "user_id": user_id_ctx.get(),
            "execution_time_ms": execution_ms_ctx.get(),
        }

        for key in ("event", "method", "status_code", "error_code", "module"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=True)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.addHandler(handler)
