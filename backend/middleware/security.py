from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from core.config import Settings, get_settings
from core.exceptions import AppException

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

# Requested pattern for phone redaction.
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-]{8,}\d)")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return repr(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value


def _request_id() -> str:
    return uuid.uuid4().hex


def _header_value(scope: dict[str, Any], name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return value.decode("latin-1")
    return None


def _normalize_origins(origins_csv: str) -> list[str]:
    origins = [o.strip() for o in (origins_csv or "").split(",") if o.strip()]
    if not origins:
        raise RuntimeError("ALLOWED_ORIGINS/CORS_ORIGINS must contain at least one origin")
    if "*" in origins:
        raise RuntimeError("Wildcard origin '*' is not allowed when credentials are enabled")
    return origins


def redact_sensitive_text(value: str) -> str:
    redacted = PHONE_PATTERN.sub("[CONTACT HIDDEN]", value)
    redacted = EMAIL_PATTERN.sub("[CONTACT HIDDEN]", redacted)
    return redacted


def redact_sensitive_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: redact_sensitive_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [redact_sensitive_payload(v) for v in payload]
    if isinstance(payload, str):
        return redact_sensitive_text(payload)
    return payload


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or _request_id()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class PayloadTooLarge(Exception):
    pass


class RequestSizeLimitMiddleware:
    """ASGI middleware that enforces Content-Length and streamed body limits."""

    def __init__(self, app, max_body_size: int):
        self.app = app
        self.max_body_size = int(max_body_size)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _header_value(scope, b"x-request-id") or _request_id()
        content_length = _header_value(scope, b"content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    await self._send_limit_response(scope, receive, send, request_id)
                    return
            except ValueError:
                await self._send_limit_response(scope, receive, send, request_id)
                return

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_size:
                    raise PayloadTooLarge()
            return message

        async def send_wrapper(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, send_wrapper)
        except PayloadTooLarge:
            if not response_started:
                await self._send_limit_response(scope, receive, send, request_id)

    async def _send_limit_response(self, scope, receive, send, request_id: str) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "success": False,
                "data": None,
                "message": "Request body too large",
                "error_code": "PAYLOAD_TOO_LARGE",
                "request_id": request_id,
            },
            headers={REQUEST_ID_HEADER: request_id},
        )
        await response(scope, receive, send)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, csp: str):
        super().__init__(app)
        self.csp = csp

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Content-Security-Policy": self.csp,
        }.items():
            if header not in response.headers:
                response.headers[header] = value
        return response


class ChatRedactionMiddleware(BaseHTTPMiddleware):
    """
    Redact contact leakage from chat/notification payloads in outgoing JSON responses.
    Applied only on chat-like endpoints to minimize overhead.
    """

    CHAT_PREFIXES = ("/api/chat", "/api/chats", "/api/assistant")

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if not path.startswith(self.CHAT_PREFIXES):
            return response
        if response.status_code >= 400:
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return response

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        redacted = redact_sensitive_payload(payload)
        new_body = json.dumps(redacted, ensure_ascii=True, default=str).encode("utf-8")
        headers = dict(response.headers)
        headers.pop("content-length", None)

        return Response(
            content=new_body,
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )


def register_global_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        request_id = getattr(request.state, "request_id", "")
        logger.warning(
            "app_exception",
            extra={
                "event": "app_exception",
                "path": request.url.path,
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "request_id": request_id,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": exc.data,
                "message": exc.message,
                "error_code": exc.error_code,
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "")
        logger.warning(
            "request_validation_error",
            extra={"event": "request_validation_error", "path": request.url.path, "request_id": request_id},
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "message": "Validation error",
                "request_id": request_id,
                "errors": _json_safe(exc.errors()),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", "")
        logger.warning(
            "http_exception",
            extra={
                "event": "http_exception",
                "path": request.url.path,
                "status_code": exc.status_code,
                "request_id": request_id,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": str(exc.detail),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "")
        logger.exception(
            "unhandled_exception",
            extra={"event": "unhandled_exception", "path": request.url.path, "request_id": request_id},
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "message": "Internal Server Error",
                "request_id": request_id,
            },
        )


def configure_security_middleware(app: FastAPI, settings: Settings | None = None) -> None:
    """
    Canonical security middleware registration:
    - explicit CORS origins only
    - request ID middleware
    - chat redaction middleware
    - global exception handlers
    """
    s = settings or get_settings()
    origins = s.allowed_origins_list() if hasattr(s, "allowed_origins_list") else _normalize_origins(
        getattr(s, "ALLOWED_ORIGINS", None) or getattr(s, "CORS_ORIGINS", "")
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        max_age=3600,
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ChatRedactionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, csp=s.SECURITY_CSP)
    app.add_middleware(RequestSizeLimitMiddleware, max_body_size=s.REQUEST_MAX_BODY_SIZE_BYTES)
    register_global_exception_handlers(app)
