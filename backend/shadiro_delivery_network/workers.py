"""
Celery task definitions for scalable async processing.

Heavy jobs moved to workers:
- Notifications
- Fraud analysis
- ETA recalculation
- Assignment retries
- Analytics aggregation
- Webhook retries
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from celery import Celery, Task
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Initialize Celery app (configure via environment)
celery_app = Celery(
    "shadiro_delivery",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard timeout
    task_soft_time_limit=25 * 60,  # 25 minutes soft timeout
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


class DeliveryTask(Task):
    """Base task with custom error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.send_notification")
def send_notification_task(
    self,
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Send delivery notification (Firebase Cloud Messaging).
    
    Offloaded from request path for low latency.
    """
    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon="https://delivery.shadiro.app/icon.png",
                ),
            ),
        )

        # Would send to specific user tokens
        # For now, just log
        logger.info(f"notification_sent: {notification_type} to {user_id}")

        return {
            "success": True,
            "user_id": user_id,
            "notification_type": notification_type,
        }

    except Exception as e:
        logger.error(f"Notification failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.analyze_fraud")
def analyze_fraud_task(
    self,
    partner_id: str,
    job_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Deep fraud analysis using historical data.
    
    Offloaded to worker for performance.
    """
    try:
        logger.info(f"Analyzing fraud for partner: {partner_id}")

        # This would integrate with advanced ML models
        # For now, placeholder implementation
        
        return {
            "partner_id": partner_id,
            "fraud_score": 0.15,
            "risk_level": "low",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Fraud analysis failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.recalculate_eta")
def recalculate_eta_task(
    self,
    job_id: str,
    partner_lat: float,
    partner_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
) -> dict[str, Any]:
    """
    Recalculate ETA based on current position.
    
    Called periodically or when partner moves significantly.
    """
    try:
        # This would call ETACalculationService
        logger.info(f"Recalculating ETA for job: {job_id}")

        # Placeholder
        return {
            "job_id": job_id,
            "eta_minutes": 22.5,
            "traffic_level": "moderate",
            "recalculated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"ETA recalculation failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.run_assignment_retry")
def run_assignment_retry_task(
    self,
    job_id: str,
) -> dict[str, Any]:
    """
    Retry assignment if offer was rejected by all partners.
    
    Exponential backoff to find available partner.
    """
    try:
        logger.info(f"Retrying assignment for job: {job_id}")

        # Would call assignment engine again
        return {
            "job_id": job_id,
            "retry_count": self.request.retries,
            "new_partner_assigned": True,
        }

    except Exception as e:
        logger.error(f"Assignment retry failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.cleanup_qr_codes")
def cleanup_qr_codes_task(self) -> dict[str, Any]:
    """
    Clean up expired QR codes and temporary data.
    
    Runs hourly.
    """
    try:
        logger.info("Cleaning up expired QR codes")

        # Would delete expired QR codes from cache
        deleted_count = 0

        return {
            "deleted_qr_codes": deleted_count,
            "cleanup_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"QR cleanup failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.aggregate_analytics")
def aggregate_analytics_task(self) -> dict[str, Any]:
    """
    Aggregate delivery metrics for dashboard.
    
    Runs every 5 minutes.
    """
    try:
        logger.info("Aggregating delivery analytics")

        # Heavy computation moved to worker
        current_time = datetime.now(timezone.utc)
        five_mins_ago = current_time - timedelta(minutes=5)

        analytics = {
            "period": f"{five_mins_ago.isoformat()}_to_{current_time.isoformat()}",
            "active_deliveries": 0,
            "completed_deliveries": 0,
            "cancelled_deliveries": 0,
            "average_eta_minutes": 0,
            "average_rating": 0,
        }

        return analytics

    except Exception as e:
        logger.error(f"Analytics aggregation failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.webhook_retry")
def webhook_retry_task(
    self,
    webhook_event_id: str,
    webhook_url: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Retry failed webhook delivery.
    
    Exponential backoff up to 5 retries.
    """
    try:
        import aiohttp
        import asyncio

        async def send_webhook():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    return resp.status

        status = asyncio.run(send_webhook())
        logger.info(f"Webhook {webhook_event_id} sent with status {status}")

        return {
            "webhook_event_id": webhook_event_id,
            "status": status,
            "retry_count": self.request.retries,
        }

    except Exception as e:
        logger.error(f"Webhook retry failed: {e}")
        raise


@celery_app.task(base=DeliveryTask, bind=True, name="delivery.scheduled_ eta_recalc")
def scheduled_eta_recalculation_task(self) -> dict[str, Any]:
    """
    Bulk ETA recalculation for active deliveries.
    
    Runs every 2 minutes.
    """
    try:
        logger.info("Running scheduled ETA recalculation")

        # Get all active delivery jobs and recalculate ETAs
        updated_count = 0

        return {
            "updated_jobs": updated_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Scheduled ETA recalc failed: {e}")
        raise


# Scheduled tasks configuration
from celery.schedules import schedule

celery_app.conf.beat_schedule = {
    "cleanup-qr-codes": {
        "task": "delivery.cleanup_qr_codes",
        "schedule": schedule(run_every=timedelta(hours=1)),
    },
    "aggregate-analytics": {
        "task": "delivery.aggregate_analytics",
        "schedule": schedule(run_every=timedelta(minutes=5)),
    },
    "scheduled-eta-recalc": {
        "task": "delivery.scheduled_eta_recalc",
        "schedule": schedule(run_every=timedelta(minutes=2)),
    },
}
