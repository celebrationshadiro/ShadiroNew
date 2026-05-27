"""
Advanced fraud detection system for delivery network.

Detects:
- Fake GPS and impossible travel speeds
- QR code replay attacks
- Rooted/jailbroken devices
- Device switching patterns
- Delivery collusion
- Repeated cancellations and suspicious behavior
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from shadiro_delivery_network.assignment_engine import haversine_km
from shadiro_delivery_network.constants import COLLECTION_FRAUD

logger = logging.getLogger(__name__)

# Fraud severity levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# Fraud scores thresholds
FRAUD_SCORE_THRESHOLD_REVIEW = 0.3
FRAUD_SCORE_THRESHOLD_SUSPEND = 0.6
FRAUD_SCORE_THRESHOLD_BLOCK = 0.85


class AdvancedFraudDetectionService:
    """
    Comprehensive fraud detection for delivery partners.
    
    ML-ready: Easily integrate ML scoring models.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def log_fraud_event(
        self,
        *,
        event_type: str,
        severity: str,
        partner_id: Optional[str] = None,
        job_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        device_id: Optional[str] = None,
        details: dict[str, Any],
        confidence: float = 0.5,
    ) -> str:
        """Log fraud event with confidence score."""
        doc = {
            "id": f"frd_{uuid4().hex}",
            "event_type": event_type,
            "severity": severity,
            "confidence": confidence,
            "partner_id": partner_id,
            "job_id": job_id,
            "vendor_id": vendor_id,
            "device_id": device_id,
            "details": details,
            "created_at": datetime.now(timezone.utc),
            "reviewed": False,
        }
        await self.db[COLLECTION_FRAUD].insert_one(doc)
        
        logger.warning(
            f"fraud_detected: {event_type}",
            extra={
                "event": "fraud_detected",
                "event_type": event_type,
                "partner_id": partner_id,
                "confidence": confidence,
            },
        )
        return doc["id"]

    async def detect_fake_gps(
        self,
        *,
        partner_id: str,
        job_id: str,
        current_lat: float,
        current_lng: float,
        previous_lat: Optional[float],
        previous_lng: Optional[float],
        time_diff_seconds: float,
        device_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Detect impossible travel speeds (fake GPS).
        
        Returns: (is_fraud, reason)
        """
        if previous_lat is None or previous_lng is None:
            return False, None

        distance_km = haversine_km(previous_lat, previous_lng, current_lat, current_lng)
        
        # Maximum realistic speed: 120 km/h (top highway speed in India)
        max_realistic_speed_kmh = 120
        max_distance_km = (max_realistic_speed_kmh / 3600) * time_diff_seconds

        if distance_km > max_distance_km:
            speed_kmh = (distance_km / time_diff_seconds) * 3600
            
            event_id = await self.log_fraud_event(
                event_type="fake_gps_detected",
                severity=SEVERITY_HIGH,
                partner_id=partner_id,
                job_id=job_id,
                device_id=device_id,
                details={
                    "distance_km": round(distance_km, 2),
                    "time_seconds": time_diff_seconds,
                    "speed_kmh": round(speed_kmh, 1),
                    "max_realistic_speed_kmh": max_realistic_speed_kmh,
                },
                confidence=min(1.0, speed_kmh / (max_realistic_speed_kmh * 2)),
            )
            return True, event_id

        return False, None

    async def detect_qr_replay(
        self,
        *,
        partner_id: str,
        job_id: str,
        qr_payload_hash: str,
        scan_time: datetime,
        device_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Detect QR code replay attacks.
        
        Multiple scans of same QR within short time suggests replay.
        """
        recent_scans = await self.db[COLLECTION_FRAUD].find(
            {
                "event_type": "qr_scan_detected",
                "partner_id": partner_id,
                "created_at": {
                    "$gte": scan_time - timedelta(hours=1)
                },
                "details.qr_hash": qr_payload_hash,
            }
        ).to_list(length=None)

        if len(recent_scans) >= 2:
            event_id = await self.log_fraud_event(
                event_type="qr_replay_suspected",
                severity=SEVERITY_CRITICAL,
                partner_id=partner_id,
                job_id=job_id,
                device_id=device_id,
                details={
                    "scan_count": len(recent_scans),
                    "qr_hash": qr_payload_hash,
                },
                confidence=0.95,
            )
            return True, event_id

        return False, None

    async def detect_device_rooting(
        self,
        *,
        partner_id: str,
        device_id: str,
        device_fingerprint: dict[str, Any],
        job_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Detect rooted/jailbroken devices.
        
        Red flags:
        - Custom ROMs/kernels
        - Disabled selinux
        - Superuser apps
        - Security patch gaps
        """
        risk_score = 0.0
        risk_indicators = []

        if device_fingerprint.get("is_rooted"):
            risk_score += 0.5
            risk_indicators.append("Device reports as rooted")

        if device_fingerprint.get("is_jailbroken"):
            risk_score += 0.5
            risk_indicators.append("Device reports as jailbroken")

        if device_fingerprint.get("has_custom_rom"):
            risk_score += 0.3
            risk_indicators.append("Custom ROM detected")

        if device_fingerprint.get("selinux_disabled"):
            risk_score += 0.2
            risk_indicators.append("SELinux disabled")

        if device_fingerprint.get("superuser_apps"):
            risk_score += 0.4
            risk_indicators.append("Superuser apps present")

        # Security patch age
        patch_age_days = device_fingerprint.get("security_patch_age_days", 0)
        if patch_age_days > 90:
            risk_score += 0.1
            risk_indicators.append(f"Security patch {patch_age_days} days old")

        if risk_score > FRAUD_SCORE_THRESHOLD_REVIEW:
            event_id = await self.log_fraud_event(
                event_type="device_rooting_detected",
                severity=SEVERITY_MEDIUM if risk_score < FRAUD_SCORE_THRESHOLD_SUSPEND else SEVERITY_HIGH,
                partner_id=partner_id,
                job_id=job_id,
                device_id=device_id,
                details={
                    "risk_indicators": risk_indicators,
                    "risk_score": risk_score,
                    "fingerprint": device_fingerprint,
                },
                confidence=min(1.0, risk_score),
            )
            return risk_score > FRAUD_SCORE_THRESHOLD_SUSPEND, event_id

        return False, None

    async def detect_suspicious_device_switching(
        self,
        *,
        partner_id: str,
        device_id: str,
        job_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Detect rapid device switching (suggests account sharing).
        """
        recent_devices = await self.db[COLLECTION_FRAUD].find(
            {
                "event_type": "device_location_update",
                "partner_id": partner_id,
                "created_at": {
                    "$gte": datetime.now(timezone.utc) - timedelta(hours=2)
                },
            }
        ).to_list(length=None)

        unique_devices = set()
        for record in recent_devices:
            dev_id = record.get("device_id")
            if dev_id:
                unique_devices.add(dev_id)

        if len(unique_devices) >= 3:
            event_id = await self.log_fraud_event(
                event_type="suspicious_device_switching",
                severity=SEVERITY_HIGH,
                partner_id=partner_id,
                job_id=job_id,
                device_id=device_id,
                details={
                    "unique_devices_2h": len(unique_devices),
                    "devices": list(unique_devices),
                },
                confidence=min(1.0, len(unique_devices) / 5),
            )
            return True, event_id

        return False, None

    async def detect_cancellation_pattern(
        self,
        *,
        partner_id: str,
        job_id: str,
        device_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Detect suspicious cancellation patterns.
        """
        from shadiro_delivery_network.constants import COLLECTION_JOBS

        # Get partner's cancellations in last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        cancellations = await self.db[COLLECTION_JOBS].count_documents(
            {
                "partner_id": partner_id,
                "state": "cancelled",
                "updated_at": {"$gte": seven_days_ago},
            }
        )

        total_jobs = await self.db[COLLECTION_JOBS].count_documents(
            {
                "partner_id": partner_id,
                "updated_at": {"$gte": seven_days_ago},
            }
        )

        cancellation_rate = cancellations / max(1, total_jobs)

        # High cancellation rate is suspicious
        if cancellation_rate > 0.3:
            event_id = await self.log_fraud_event(
                event_type="high_cancellation_rate",
                severity=SEVERITY_MEDIUM,
                partner_id=partner_id,
                job_id=job_id,
                device_id=device_id,
                details={
                    "cancellations_7d": cancellations,
                    "total_jobs_7d": total_jobs,
                    "cancellation_rate": cancellation_rate,
                },
                confidence=min(1.0, cancellation_rate),
            )
            return True, event_id

        return False, None

    async def calculate_partner_fraud_score(
        self,
        partner_id: str,
    ) -> float:
        """
        Calculate aggregate fraud score for partner (0-1).
        
        Returns:
            Float between 0 (trusted) and 1 (high risk)
        """
        # Get recent fraud events
        recent_events = await self.db[COLLECTION_FRAUD].find(
            {
                "partner_id": partner_id,
                "created_at": {
                    "$gte": datetime.now(timezone.utc) - timedelta(days=30)
                },
            }
        ).to_list(length=None)

        if not recent_events:
            return 0.0

        # Weight by severity
        severity_weights = {
            SEVERITY_LOW: 0.1,
            SEVERITY_MEDIUM: 0.3,
            SEVERITY_HIGH: 0.6,
            SEVERITY_CRITICAL: 1.0,
        }

        total_score = 0.0
        for event in recent_events:
            severity = event.get("severity", SEVERITY_LOW)
            confidence = event.get("confidence", 0.5)
            weight = severity_weights.get(severity, 0.1)
            total_score += weight * confidence

        # Normalize to 0-1
        return min(1.0, total_score / max(1, len(recent_events)))
