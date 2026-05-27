"""
Security hardening for delivery network.

Implementation:
- End-to-end encryption for sensitive data
- Signed delivery events
- Device fingerprinting
- Anti-tampering checks
- Certificate pinning preparation
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class DeliverySecurityService:
    """
    Security hardening for delivery operations.
    """

    def __init__(self, encryption_key: str):
        """
        Initialize with encryption key (32-byte base64 encoded).
        
        Generate via: from cryptography.fernet import Fernet; Fernet.generate_key()
        """
        self.cipher = Fernet(encryption_key.encode())
        self.hmac_secret = encryption_key

    def encrypt_sensitive_delivery_data(
        self,
        data: dict[str, Any],
    ) -> str:
        """
        Encrypt sensitive delivery information.
        
        Used for storing PII in database.
        """
        json_str = json.dumps(data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()

    def decrypt_sensitive_delivery_data(self, encrypted: str) -> dict[str, Any]:
        """Decrypt sensitive delivery data."""
        try:
            decrypted = self.cipher.decrypt(encrypted.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def sign_delivery_event(
        self,
        event_data: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Sign delivery event for integrity verification.
        
        Returns: (event_json, signature)
        """
        event_json = json.dumps(event_data, separators=(",", ":"), sort_keys=True)
        signature = hmac.new(
            self.hmac_secret.encode(),
            event_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        return event_json, signature

    def verify_delivery_event_signature(
        self,
        event_json: str,
        signature: str,
    ) -> bool:
        """Verify delivery event signature."""
        expected_signature = hmac.new(
            self.hmac_secret.encode(),
            event_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def generate_device_fingerprint_hash(
        self,
        device_id: str,
        device_model: str,
        os_version: str,
        app_version: str,
        serial_number: Optional[str] = None,
    ) -> str:
        """
        Generate cryptographic hash of device fingerprint.
        
        Used to detect account sharing or device spoofing.
        """
        fingerprint_parts = [
            device_id,
            device_model,
            os_version,
            app_version,
        ]

        if serial_number:
            fingerprint_parts.append(serial_number)

        fingerprint_str = "|".join(fingerprint_parts)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    def detect_tampering(
        self,
        original_hash: str,
        current_device_data: dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """
        Detect if device has been tampered with or spoofed.
        
        Returns: (is_tampered, tampering_reason)
        """
        current_hash = self.generate_device_fingerprint_hash(
            device_id=current_device_data.get("device_id", ""),
            device_model=current_device_data.get("device_model", ""),
            os_version=current_device_data.get("os_version", ""),
            app_version=current_device_data.get("app_version", ""),
        )

        if current_hash != original_hash:
            return True, "device_fingerprint_mismatch"

        return False, None

    def generate_delivery_receipt(
        self,
        job_id: str,
        partner_id: str,
        timestamp: datetime,
        location_lat: float,
        location_lng: float,
    ) -> dict[str, Any]:
        """
        Generate signed delivery receipt.
        
        Proof of delivery with integrity verification.
        """
        receipt_data = {
            "job_id": job_id,
            "partner_id": partner_id,
            "timestamp": timestamp.isoformat(),
            "location": {
                "lat": location_lat,
                "lng": location_lng,
            },
            "receipt_id": f"rcpt_{uuid4().hex}",
        }

        receipt_json, signature = self.sign_delivery_event(receipt_data)

        return {
            "receipt_data": receipt_json,
            "signature": signature,
            "receipt_id": receipt_data["receipt_id"],
        }

    def get_certificate_pinning_config(self) -> dict[str, Any]:
        """
        Get certificate pinning configuration for mobile apps.
        
        Prevents man-in-the-middle attacks.
        """
        return {
            "pinning_enabled": True,
            "pins": [
                {
                    "domain": "delivery.shadiro.app",
                    "public_key_hash": "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                    # Replace with actual certificate pin
                },
            ],
            "backup_pins": [
                {
                    "domain": "delivery.shadiro.app",
                    "public_key_hash": "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=",
                    # Backup pin for certificate rotation
                },
            ],
            "check_subdomains": True,
            "include_subdomains": True,
            "max_age": 31536000,  # 1 year
        }

    def get_api_security_headers(self) -> dict[str, str]:
        """
        Get recommended security headers for delivery APIs.
        """
        return {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' maps.googleapis.com; style-src 'self' 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
        }

    def get_data_protection_guidelines(self) -> dict[str, Any]:
        """
        Guidelines for handling sensitive delivery data.
        """
        return {
            "pii_fields": [
                "customer_phone",
                "customer_email",
                "customer_address",
                "partner_bank_details",
                "partner_aadhar",
                "partner_pan",
            ],
            "encryption_required": True,
            "minimum_retention_days": 90,
            "maximum_retention_days": 365,
            "access_logging": True,
            "audit_required": True,
            "anonymization_after_days": 180,
        }
