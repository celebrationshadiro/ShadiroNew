from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from shadiro_delivery_network.constants import COLLECTION_FRAUD

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Heuristic fraud logging; extend with ML / rules engine without touching delivery core."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db

    async def log(
        self,
        *,
        event_type: str,
        severity: str,
        job_id: Optional[str],
        partner_id: Optional[str],
        vendor_id: Optional[str],
        details: dict[str, Any],
        device_id: Optional[str] = None,
    ) -> str:
        doc = {
            "id": f"frd_{uuid4().hex}",
            "event_type": event_type,
            "severity": severity,
            "job_id": job_id,
            "partner_id": partner_id,
            "vendor_id": vendor_id,
            "device_id": device_id,
            "details": details,
            "created_at": datetime.now(timezone.utc),
        }
        await self._db[COLLECTION_FRAUD].insert_one(doc)
        logger.info(
            "delivery_fraud_event",
            extra={"event": "delivery_fraud_event", "event_type": event_type, "job_id": job_id},
        )
        return str(doc["id"])

    async def evaluate_qr_scan_context(
        self,
        *,
        job_id: str,
        partner_id: str,
        vendor_lat: Optional[float],
        vendor_lng: Optional[float],
        scan_lat: Optional[float],
        scan_lng: Optional[float],
        client_ts: Optional[int],
        server_ts: int,
        device_id: Optional[str],
    ) -> tuple[bool, list[str]]:
        """
        Returns (ok, reasons). Non-fatal warnings still return ok=True but should be logged.
        """
        reasons: list[str] = []
        if client_ts is not None and abs(server_ts - int(client_ts)) > 180:
            await self.log(
                event_type="qr_timestamp_skew",
                severity="medium",
                job_id=job_id,
                partner_id=partner_id,
                vendor_id=None,
                details={"skew_seconds": abs(server_ts - int(client_ts))},
                device_id=device_id,
            )
            reasons.append("timestamp_skew")

        if (
            vendor_lat is not None
            and vendor_lng is not None
            and scan_lat is not None
            and scan_lng is not None
        ):
            dist_m = _haversine_m(vendor_lat, vendor_lng, scan_lat, scan_lng)
            if dist_m > 500:
                await self.log(
                    event_type="qr_geo_mismatch",
                    severity="high",
                    job_id=job_id,
                    partner_id=partner_id,
                    vendor_id=None,
                    details={"distance_m": round(dist_m, 1)},
                    device_id=device_id,
                )
                return False, reasons + ["geo_mismatch"]

        return True, reasons


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371000.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlmb / 2) ** 2
    return 2 * r * asin(sqrt(a))
