"""
Push notification infrastructure (Firebase Cloud Messaging + APNs).

Categories:
- Silent delivery updates
- Real-time alerts
- Partner notifications
- Fraud alerts
- Escalation alerts
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Unified push notification service.
    
    Supports Firebase Cloud Messaging (Android) and APNs (iOS).
    """

    def __init__(self, fcm_credentials_path: Optional[str] = None):
        self.fcm_credentials_path = fcm_credentials_path
        # Firebase client would be initialized here

    async def send_delivery_assignment(
        self,
        partner_user_id: str,
        job_id: str,
        pickup_address: str,
        dropoff_address: str,
        estimated_earnings_rupees: float,
    ) -> bool:
        """
        Send delivery assignment notification to partner.
        
        Category: ACTION_REQUIRED
        """
        notification_data = {
            "type": "delivery_assignment",
            "job_id": job_id,
            "title": "New Delivery Available",
            "body": f"₹{estimated_earnings_rupees:.0f} • {pickup_address} → {dropoff_address}",
            "action_url": f"/delivery/{job_id}/offer",
            "priority": "high",
            "ttl": 45,  # 45 second offer window
        }

        return await self._send_notification(
            user_id=partner_user_id,
            notification_data=notification_data,
            silent=False,
            action_buttons=[
                {
                    "id": "accept",
                    "title": "Accept",
                },
                {
                    "id": "reject",
                    "title": "Reject",
                },
            ],
        )

    async def send_delivery_pickup_reminder(
        self,
        partner_user_id: str,
        job_id: str,
        pickup_time: str,
    ) -> bool:
        """
        Send pickup reminder 5 minutes before.
        """
        notification_data = {
            "type": "pickup_reminder",
            "job_id": job_id,
            "title": "Pickup Reminder",
            "body": f"Pickup at {pickup_time}",
            "priority": "normal",
        }

        return await self._send_notification(
            user_id=partner_user_id,
            notification_data=notification_data,
            silent=False,
        )

    async def send_delivery_update(
        self,
        customer_user_id: str,
        job_id: str,
        status: str,
        eta_minutes: int,
    ) -> bool:
        """
        Send delivery status update to customer.
        
        Category: INFORMATIONAL (silent update)
        """
        status_messages = {
            "assigned": "Partner found! Heading your way",
            "pickup_scanned": "Package picked up",
            "en_route": f"On the way • {eta_minutes} min away",
            "arriving": "Arriving soon",
            "delivered": "Delivered! ✓",
        }

        notification_data = {
            "type": "delivery_update",
            "job_id": job_id,
            "status": status,
            "body": status_messages.get(status, "Delivery update"),
            "priority": "normal",
        }

        # Silent update if en_route, normal otherwise
        return await self._send_notification(
            user_id=customer_user_id,
            notification_data=notification_data,
            silent=(status == "en_route"),
        )

    async def send_fraud_alert(
        self,
        admin_user_id: str,
        fraud_type: str,
        partner_id: str,
        severity: str,
    ) -> bool:
        """
        Send fraud alert to admin.
        """
        severity_icons = {
            "low": "⚠️",
            "medium": "⚠️⚠️",
            "high": "🚨",
            "critical": "🚨🚨🚨",
        }

        notification_data = {
            "type": "fraud_alert",
            "partner_id": partner_id,
            "title": f"{severity_icons.get(severity, '⚠️')} Fraud Alert",
            "body": f"{fraud_type} detected • {partner_id}",
            "priority": "high",
            "action_url": f"/admin/fraud/{partner_id}",
        }

        return await self._send_notification(
            user_id=admin_user_id,
            notification_data=notification_data,
            silent=False,
        )

    async def send_escalation_alert(
        self,
        admin_user_id: str,
        job_id: str,
        reason: str,
    ) -> bool:
        """
        Send escalation alert (delivery taking too long, etc.).
        """
        notification_data = {
            "type": "escalation_alert",
            "job_id": job_id,
            "title": "Delivery Escalation",
            "body": reason,
            "priority": "high",
            "action_url": f"/admin/deliveries/{job_id}",
        }

        return await self._send_notification(
            user_id=admin_user_id,
            notification_data=notification_data,
            silent=False,
        )

    async def _send_notification(
        self,
        user_id: str,
        notification_data: dict[str, Any],
        *,
        silent: bool = False,
        action_buttons: Optional[list[dict[str, str]]] = None,
    ) -> bool:
        """
        Internal method to send notification via FCM/APNs.
        """
        try:
            # In production:
            # 1. Get user's device tokens from database
            # 2. Split tokens by platform (Android/iOS)
            # 3. Send via appropriate service
            
            logger.info(
                f"notification_sent: {notification_data.get('type')} to {user_id}",
                extra={
                    "event": "notification_sent",
                    "user_id": user_id,
                    "type": notification_data.get("type"),
                },
            )

            return True

        except Exception as e:
            logger.error(f"Push notification failed: {e}")
            return False


class NotificationCategory:
    """Predefined notification categories for handling."""

    ACTION_REQUIRED = "action_required"  # Delivery offer, approval needed
    INFORMATIONAL = "informational"  # Status updates, silent updates
    ALERT = "alert"  # Fraud, escalation
    REMINDER = "reminder"  # Upcoming pickups, deliveries


class NotificationTemplate:
    """Reusable notification templates."""

    @staticmethod
    def format_time_remaining(minutes: int) -> str:
        """Format remaining time for display."""
        if minutes < 1:
            return "< 1 min"
        elif minutes == 1:
            return "1 min"
        elif minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"

    @staticmethod
    def format_earnings(rupees: float) -> str:
        """Format earnings amount."""
        if rupees >= 1000:
            return f"₹{rupees/1000:.1f}k"
        return f"₹{rupees:.0f}"

    @staticmethod
    def get_delivery_status_emoji(status: str) -> str:
        """Get emoji for delivery status."""
        emojis = {
            "pending": "⏳",
            "assigned": "👤",
            "pickup_scanned": "📦",
            "en_route": "🚗",
            "arriving": "📍",
            "delivered": "✓",
            "cancelled": "❌",
        }
        return emojis.get(status, "•")
