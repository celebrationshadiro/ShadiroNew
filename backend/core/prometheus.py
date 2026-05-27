import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

    _PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency fallback
    _PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _NoopMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, value: float = 1.0):
            return None

        def observe(self, value: float):
            return None

    def Counter(*args, **kwargs):  # type: ignore[no-redef]
        return _NoopMetric()

    def Histogram(*args, **kwargs):  # type: ignore[no-redef]
        return _NoopMetric()

    def generate_latest() -> bytes:  # type: ignore[no-redef]
        return b"# prometheus_client not installed\n"


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error responses",
    ["method", "path", "status_class"],
)

WEBHOOK_EVENTS_TOTAL = Counter(
    "webhook_events_total",
    "Total Razorpay webhook events processed",
    ["event", "outcome"],
)

PAYMENT_PROCESSING_LATENCY = Histogram(
    "payment_processing_latency_seconds",
    "Latency for payment and payout processing flows",
    ["flow"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

AUTH_FAILURES_TOTAL = Counter(
    "auth_failures_total",
    "Total authentication and authorization failures",
    ["reason", "endpoint"],
)


def _resolve_route_path(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        response = None
        method = request.method

        try:
            response = await call_next(request)
            return response
        finally:
            elapsed = time.perf_counter() - started_at
            path = _resolve_route_path(request)
            REQUEST_COUNT.labels(method=method, path=path).inc()
            REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)

            status_code = getattr(response, "status_code", 500)
            if status_code >= 400:
                status_class = "4xx" if 400 <= status_code < 500 else "5xx"
                ERROR_COUNT.labels(
                    method=method,
                    path=path,
                    status_class=status_class,
                ).inc()


def metrics_response() -> Response:
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def increment_webhook_event(event: str, outcome: str) -> None:
    WEBHOOK_EVENTS_TOTAL.labels(event=event, outcome=outcome).inc()


def observe_payment_latency(flow: str, seconds: float) -> None:
    PAYMENT_PROCESSING_LATENCY.labels(flow=flow).observe(seconds)


def increment_auth_failure(reason: str, endpoint: str) -> None:
    AUTH_FAILURES_TOTAL.labels(reason=reason, endpoint=endpoint).inc()
