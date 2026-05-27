import logging
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.logging import clear_request_context, set_request_context
from core.security import decode_access_token

logger = logging.getLogger(__name__)


def _extract_user_id(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except Exception:
        return None


class RequestContextLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        user_id = _extract_user_id(request)
        path = request.url.path

        set_request_context(request_id=rid, path=path, user_id=user_id, execution_ms=0.0)
        logger.info(
            "incoming_request",
            extra={
                "event": "request_incoming",
                "method": request.method,
            },
        )

        response: Optional[Response] = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
            set_request_context(execution_ms=elapsed_ms)
            logger.info(
                "request_completed",
                extra={
                    "event": "request_completed",
                    "method": request.method,
                    "status_code": getattr(response, "status_code", 500),
                },
            )
            if response is not None:
                response.headers["X-Request-ID"] = rid
            clear_request_context()
