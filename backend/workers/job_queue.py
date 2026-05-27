from __future__ import annotations

import asyncio
import logging
from typing import Any

# Import all background tasks
from workers.tasks.booking_tasks import update_vendor_booking_count, release_expired_locks
from workers.tasks.notification_tasks import (
    send_booking_confirmation_email_job,
    send_vendor_new_booking_alert,
    send_quote_accepted_notification,
    send_payment_failure_email,
)
from workers.tasks.maintenance_tasks import (
    release_expired_booking_locks,
    update_vendor_availability_cache,
    calculate_vendor_ratings,
    expire_old_quotes,
)

logger = logging.getLogger(__name__)


async def update_vendor_response_metrics_placeholder(vendor_id: str) -> None:
    """Updates response SLA metrics for a vendor profile."""
    # Placeholder for vendor response SLA tracking
    logger.info(f"Recalculating response SLA metrics for vendor {vendor_id}")


# Background Jobs Registry
JOB_REGISTRY = {
    # Booking confirmed triggers
    "send_booking_confirmation_email": send_booking_confirmation_email_job,
    "send_vendor_new_booking_alert": send_vendor_new_booking_alert,
    "update_vendor_booking_count": update_vendor_booking_count,

    # Quote accepted triggers
    "send_quote_accepted_notification": send_quote_accepted_notification,
    "update_vendor_response_metrics": update_vendor_response_metrics_placeholder,

    # Payment failed triggers
    "send_payment_failure_email": send_payment_failure_email,
    "release_expired_locks": release_expired_locks,

    # Cron / Scheduled maintenance jobs
    "release_expired_booking_locks": release_expired_booking_locks,
    "update_vendor_availability_cache": update_vendor_availability_cache,
    "calculate_vendor_ratings": calculate_vendor_ratings,
    "expire_old_quotes": expire_old_quotes,
}


async def enqueue_job(job_name: str, *args, **kwargs) -> None:
    """
    Enqueues and detaches a background job to run concurrently
    outside of the HTTP request-response critical path.
    """
    task_func = JOB_REGISTRY.get(job_name)
    if not task_func:
        logger.warning(f"Unregistered background job enqueued: '{job_name}'")
        return

    logger.info(f"Enqueuing background job '{job_name}' with args={args}, kwargs={kwargs}")
    asyncio.create_task(_run_job_safely(job_name, task_func, *args, **kwargs))


async def _run_job_safely(name: str, func: Any, *args, **kwargs) -> None:
    try:
        await func(*args, **kwargs)
        logger.info(f"Background job '{name}' executed successfully.")
    except Exception as e:
        logger.error(f"Background job '{name}' execution failed: {e}", exc_info=True)
