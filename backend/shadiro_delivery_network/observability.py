"""
System observability for delivery network.

Includes:
- Prometheus metrics
- Grafana dashboard specs
- Sentry error tracking
- Distributed tracing
- Real-time operations monitoring
- Queue monitoring
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Optional

from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)

# ============== PROMETHEUS METRICS ==============

# Delivery Job Metrics
delivery_jobs_created = Counter(
    "delivery_jobs_created_total",
    "Total delivery jobs created",
    ["source_type", "logistics_tier"],
)

delivery_jobs_completed = Counter(
    "delivery_jobs_completed_total",
    "Total completed deliveries",
    ["completion_status", "tier"],
)

delivery_jobs_active = Gauge(
    "delivery_jobs_active",
    "Currently active delivery jobs",
    ["state", "tier"],
)

delivery_job_duration = Histogram(
    "delivery_job_duration_minutes",
    "Delivery job duration in minutes",
    ["tier"],
    buckets=[5, 10, 15, 20, 30, 45, 60, 90, 120],
)

# ETA Metrics
eta_accuracy = Histogram(
    "delivery_eta_accuracy_ratio",
    "ETA accuracy (actual/estimated)",
    ["source"],
    buckets=[0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0],
)

eta_calculation_time = Histogram(
    "eta_calculation_duration_ms",
    "Time to calculate ETA",
    ["method"],
    buckets=[10, 50, 100, 250, 500, 1000, 2000],
)

# Partner Metrics
partner_assignments = Counter(
    "partner_assignments_total",
    "Total delivery assignments",
    ["assignment_reason", "tier"],
)

partner_acceptance_rate = Gauge(
    "partner_acceptance_rate",
    "Partner acceptance rate",
    ["partner_id"],
)

partner_active_jobs = Gauge(
    "partner_active_jobs",
    "Active jobs per partner",
    ["partner_id", "status"],
)

partner_fraud_score = Gauge(
    "partner_fraud_score",
    "Partner fraud risk score",
    ["partner_id"],
)

# Fraud Metrics
fraud_events_detected = Counter(
    "fraud_events_detected_total",
    "Total fraud events detected",
    ["event_type", "severity"],
)

fraud_detection_latency = Histogram(
    "fraud_detection_latency_ms",
    "Time to detect fraud",
    ["event_type"],
    buckets=[10, 50, 100, 250, 500],
)

# Assignment Engine Metrics
assignment_candidates_evaluated = Histogram(
    "assignment_candidates_evaluated",
    "Number of candidates evaluated per assignment",
    buckets=[1, 5, 10, 25, 50, 100],
)

assignment_engine_latency = Histogram(
    "assignment_engine_latency_ms",
    "Assignment engine execution time",
    buckets=[50, 100, 250, 500, 1000],
)

# WebSocket/Realtime Metrics
websocket_connections = Gauge(
    "websocket_connections_active",
    "Active WebSocket connections",
    ["connection_type"],
)

realtime_message_latency = Histogram(
    "realtime_message_latency_ms",
    "Latency to broadcast realtime message",
    buckets=[10, 50, 100, 250, 500],
)

# API Metrics
delivery_api_requests = Counter(
    "delivery_api_requests_total",
    "Total delivery API requests",
    ["endpoint", "method", "status"],
)

delivery_api_latency = Histogram(
    "delivery_api_latency_ms",
    "Delivery API request latency",
    ["endpoint"],
    buckets=[10, 50, 100, 250, 500, 1000, 2000],
)

# Queue Metrics
celery_queue_length = Gauge(
    "celery_queue_length",
    "Number of pending Celery tasks",
    ["queue_name"],
)

celery_task_duration = Histogram(
    "celery_task_duration_ms",
    "Celery task execution time",
    ["task_name"],
    buckets=[100, 500, 1000, 5000, 10000, 30000],
)


class ObservabilityService:
    """
    Centralized observability for delivery network.
    """

    def __init__(self, sentry_dsn: Optional[str] = None):
        self.sentry_dsn = sentry_dsn
        if sentry_dsn:
            self._init_sentry()

    def _init_sentry(self) -> None:
        """Initialize Sentry for error tracking."""
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=self.sentry_dsn,
                traces_sample_rate=0.1,  # Sample 10% of transactions
                environment="production",
            )
            logger.info("Sentry initialized")
        except Exception as e:
            logger.error(f"Sentry init failed: {e}")

    @asynccontextmanager
    async def track_api_request(self, endpoint: str, method: str):
        """Track API request metrics."""
        start_time = time.time()
        try:
            yield
            status = 200
        except Exception as e:
            status = 500
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            delivery_api_latency.labels(endpoint=endpoint).observe(duration_ms)
            delivery_api_requests.labels(
                endpoint=endpoint,
                method=method,
                status=status,
            ).inc()

    @asynccontextmanager
    async def track_assignment_engine(self, tier: str):
        """Track assignment engine execution."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            assignment_engine_latency.observe(duration_ms)

    @asynccontextmanager
    async def track_eta_calculation(self, method: str):
        """Track ETA calculation metrics."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            eta_calculation_time.labels(method=method).observe(duration_ms)

    @asynccontextmanager
    async def track_fraud_detection(self, event_type: str):
        """Track fraud detection execution."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            fraud_detection_latency.labels(event_type=event_type).observe(duration_ms)

    def record_delivery_job_created(
        self,
        source_type: str,
        logistics_tier: str,
    ) -> None:
        """Record new delivery job creation."""
        delivery_jobs_created.labels(
            source_type=source_type,
            logistics_tier=logistics_tier,
        ).inc()

    def record_delivery_completed(
        self,
        completion_status: str,
        tier: str,
        duration_minutes: float,
    ) -> None:
        """Record delivery completion."""
        delivery_jobs_completed.labels(
            completion_status=completion_status,
            tier=tier,
        ).inc()
        delivery_job_duration.labels(tier=tier).observe(duration_minutes)

    def record_fraud_detected(
        self,
        event_type: str,
        severity: str,
    ) -> None:
        """Record fraud detection event."""
        fraud_events_detected.labels(
            event_type=event_type,
            severity=severity,
        ).inc()

    def record_eta_accuracy(
        self,
        estimated_minutes: float,
        actual_minutes: float,
        source: str = "google_maps",
    ) -> None:
        """Record ETA accuracy ratio."""
        if actual_minutes > 0:
            ratio = estimated_minutes / actual_minutes
            eta_accuracy.labels(source=source).observe(ratio)


class GrafanaDashboardSpec:
    """Grafana dashboard specification for delivery network."""

    @staticmethod
    def get_dashboard_json() -> dict[str, Any]:
        """Get Grafana dashboard JSON spec."""
        return {
            "title": "Shadiro Delivery Network",
            "panels": [
                {
                    "title": "Active Deliveries",
                    "targets": [
                        {
                            "expr": "delivery_jobs_active",
                        }
                    ],
                },
                {
                    "title": "ETA Accuracy",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, delivery_eta_accuracy_ratio)",
                        }
                    ],
                },
                {
                    "title": "Partner Acceptance Rate",
                    "targets": [
                        {
                            "expr": "partner_acceptance_rate",
                        }
                    ],
                },
                {
                    "title": "Fraud Events",
                    "targets": [
                        {
                            "expr": "rate(fraud_events_detected_total[5m])",
                        }
                    ],
                },
                {
                    "title": "API Latency P95",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, delivery_api_latency_ms)",
                        }
                    ],
                },
                {
                    "title": "Assignment Engine Performance",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.99, assignment_engine_latency_ms)",
                        }
                    ],
                },
            ],
        }


class DistributedTracingConfig:
    """Configuration for distributed tracing (Jaeger/OpenTelemetry)."""

    @staticmethod
    def get_tracer_config() -> dict[str, Any]:
        """Get OpenTelemetry tracer configuration."""
        return {
            "service_name": "shadiro-delivery",
            "exporter": "jaeger",
            "jaeger_host": "localhost",
            "jaeger_port": 6831,
            "sampler": {
                "type": "probabilistic",
                "param": 0.1,  # Sample 10%
            },
            "instrumentation": {
                "fastapi": True,
                "sqlalchemy": True,
                "redis": True,
                "celery": True,
            },
        }
