from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


def success_response(data: Any, message: str = "", request_id: str = "") -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "message": message,
        "request_id": request_id,
    }


def error_response(message: str, status_code: int, request_id: str = "") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "message": message,
            "request_id": request_id,
        },
    )


def _is_envelope(payload: Any) -> bool:
    return isinstance(payload, dict) and {"success", "data", "message", "request_id"}.issubset(payload.keys())


class EnvelopeResponseMiddleware(BaseHTTPMiddleware):
    """
    Auto-wraps JSON responses under /api into canonical response envelope.
    Preserves already wrapped responses and ensures request_id is attached.
    """

    async def dispatch(self, request, call_next):
        request_id = getattr(request.state, "request_id", "") or uuid4().hex
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        if not request.url.path.startswith("/api"):
            return response

        content_type = str(response.headers.get("content-type", "")).lower()
        if "application/json" not in content_type:
            return response
            
        # Prevent Out-Of-Memory (OOM) on large payloads
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > 5 * 1024 * 1024:  # 5MB Limit
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            wrapped = success_response(None, request_id=request_id)
            return JSONResponse(status_code=response.status_code, content=wrapped, headers=dict(response.headers))

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        if _is_envelope(payload):
            if not payload.get("request_id"):
                payload["request_id"] = request_id
            payload.setdefault("message", "")
            return JSONResponse(status_code=response.status_code, content=payload, headers=dict(response.headers))

        wrapped = success_response(payload, request_id=request_id)
        return JSONResponse(status_code=response.status_code, content=wrapped, headers=dict(response.headers))
