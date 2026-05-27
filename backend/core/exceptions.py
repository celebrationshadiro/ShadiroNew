from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@dataclass
class AppException(Exception):
    message: str
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "APP_ERROR"
    data: Optional[dict[str, Any]] = None


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", data: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            data=data,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden", data: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            data=data,
        )


class NotFoundError(AppException):
    def __init__(self, message: str = "Not found", data: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            data=data,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict", data: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            data=data,
        )


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error", data: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            data=data,
        )


logger = logging.getLogger(__name__)


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


def register_exception_handlers(app: FastAPI) -> None:
    """
    Backward-compatible exception registration used by legacy server wiring.
    """

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        request_id = getattr(request.state, "request_id", "")
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
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "")
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
    async def handle_http_exception(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", "")
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
    async def handle_unexpected_exception(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "")
        logger.exception("unhandled_exception", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "message": "Internal Server Error",
                "request_id": request_id,
            },
        )
