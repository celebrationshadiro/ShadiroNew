from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from shadiro_delivery_network.constants import COLLECTION_QR_SESSIONS


@dataclass
class QRIssueResult:
    jti: str
    payload_b64: str
    expires_at: datetime


class QRService:
    """
    Single-use, time-bound QR sessions bound to order(job)+vendor+partner.
    Payload is tokenized (opaque blob) — screenshot replay fails on consume + rotation.
    """

    def __init__(self, db: AsyncIOMotorDatabase, hmac_secret: str) -> None:
        self._db = db
        self._secret = hmac_secret.encode("utf-8")

    def _sign(self, body: dict[str, Any]) -> str:
        canonical = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hmac.new(self._secret, canonical, hashlib.sha256).hexdigest()

    async def issue_vendor_pickup_qr(
        self,
        *,
        job_id: str,
        vendor_id: str,
        partner_id: str,
        ttl_seconds: int = 180,
        rotate: bool = True,
    ) -> QRIssueResult:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)
        jti = uuid4().hex
        if rotate:
            await self._db[COLLECTION_QR_SESSIONS].update_many(
                {
                    "job_id": job_id,
                    "vendor_id": vendor_id,
                    "consumed_at": None,
                },
                {"$set": {"superseded_at": now}},
            )
        body_core = {
            "v": 1,
            "jti": jti,
            "job_id": job_id,
            "vendor_id": vendor_id,
            "partner_id": partner_id,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }
        sig = self._sign(body_core)
        envelope = {**body_core, "sig": sig}
        raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        await self._db[COLLECTION_QR_SESSIONS].insert_one(
            {
                "jti": jti,
                "job_id": job_id,
                "vendor_id": vendor_id,
                "partner_id": partner_id,
                "payload_fingerprint": hashlib.sha256(raw).hexdigest(),
                "issued_at": now,
                "expires_at": expires,
                "consumed_at": None,
                "superseded_at": None,
            }
        )
        return QRIssueResult(jti=jti, payload_b64=payload_b64, expires_at=expires)

    def decode_payload_b64(self, payload_b64: str) -> dict[str, Any]:
        pad = "=" * (-len(payload_b64) % 4)
        raw = base64.urlsafe_b64decode(payload_b64 + pad)
        return json.loads(raw.decode("utf-8"))

    def verify_signature(self, envelope: dict[str, Any]) -> bool:
        env = dict(envelope)
        sig = env.pop("sig", None)
        if not sig:
            return False
        expected = self._sign(env)
        return hmac.compare_digest(expected, sig)

    async def consume_if_valid(
        self,
        *,
        envelope: dict[str, Any],
        expected_partner_id: str,
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        if not self.verify_signature(dict(envelope)):
            return False, "invalid_signature", None
        jti = str(envelope.get("jti") or "")
        job_id = str(envelope.get("job_id") or "")
        vendor_id = str(envelope.get("vendor_id") or "")
        partner_id = str(envelope.get("partner_id") or "")
        if partner_id != str(expected_partner_id):
            return False, "partner_mismatch", None
        now = datetime.now(timezone.utc)
        doc = await self._db[COLLECTION_QR_SESSIONS].find_one_and_update(
            {
                "jti": jti,
                "job_id": job_id,
                "vendor_id": vendor_id,
                "partner_id": partner_id,
                "consumed_at": None,
                "superseded_at": None,
                "expires_at": {"$gt": now},
            },
            {"$set": {"consumed_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            return False, "expired_or_used_or_rotated", None
        return True, "ok", doc
