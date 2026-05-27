from __future__ import annotations

import logging

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class BookingEngineErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/booking-engine"):
            return await call_next(request)

        try:
            return await call_next(request)
        except HTTPException as exc:
            logger.warning(
                "booking_engine_http_error",
                extra={"event": "booking_engine_http_error", "status_code": exc.status_code},
            )
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        except Exception:
            logger.exception("booking_engine_unhandled_error", extra={"event": "booking_engine_unhandled_error"})
            return JSONResponse(status_code=500, content={"detail": "Booking engine internal error"})
