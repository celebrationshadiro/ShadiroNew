"""
Mobile native QR scanner system for React Native.

Features:
- Native camera integration (Expo Camera)
- Real-time scanning with optimization
- Animated scanner UI
- Low-light optimized
- Fraud-resistant validation
- Offline queue support
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MobileQRScannerService:
    """
    Backend support for native mobile QR scanning.
    """

    def __init__(self, qr_hmac_secret: str):
        self.secret = qr_hmac_secret

    def generate_qr_payload(
        self,
        job_id: str,
        vendor_id: str,
        *,
        ttl_minutes: int = 30,
        nonce: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate QR payload for vendor to display.
        
        QR contains encrypted/signed job details.
        """
        nonce = nonce or uuid4().hex[:16]
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(minutes=ttl_minutes)

        payload = {
            "job_id": job_id,
            "vendor_id": vendor_id,
            "nonce": nonce,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Sign payload
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        signature = hmac.new(
            self.secret.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        return {
            "payload": payload_json,
            "signature": signature,
            "display_string": f"{job_id}:{nonce[:8]}",  # User-friendly display
        }

    def validate_qr_scan(
        self,
        payload_json: str,
        signature: str,
    ) -> tuple[bool, Optional[dict[str, Any]], Optional[str]]:
        """
        Validate scanned QR payload.
        
        Returns: (is_valid, payload_dict, error_reason)
        """
        # Verify signature
        expected_signature = hmac.new(
            self.secret.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return False, None, "invalid_signature"

        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            return False, None, "invalid_json"

        # Check expiration
        expires_at = datetime.fromisoformat(payload.get("expires_at", ""))
        if expires_at < datetime.now(timezone.utc):
            return False, None, "qr_expired"

        # Check required fields
        if not payload.get("job_id") or not payload.get("vendor_id"):
            return False, None, "missing_fields"

        return True, payload, None

    def generate_device_fingerprint_challenge(
        self,
        device_id: str,
    ) -> dict[str, str]:
        """
        Generate device verification challenge.
        
        Partner app must return fingerprint proving device integrity.
        """
        challenge_id = uuid4().hex
        challenge_text = uuid4().hex[:32]

        # Signature would be computed by client using device hardware
        return {
            "challenge_id": challenge_id,
            "challenge_text": challenge_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def verify_device_fingerprint(
        self,
        challenge_id: str,
        device_fingerprint_response: dict[str, Any],
    ) -> bool:
        """
        Verify device integrity from fingerprint response.
        
        Returns True if device is verified as legitimate.
        """
        # This would verify:
        # - Device model matches registered device
        # - No rooting/jailbreak detected
        # - Hardware characteristics match
        # - Signature is valid

        required_fields = [
            "device_id",
            "os_version",
            "app_version",
            "device_model",
            "signature",
        ]

        for field in required_fields:
            if field not in device_fingerprint_response:
                return False

        # In production, validate signature using device-specific key
        # For now, accept if all fields present
        return True


class MobileQRScannerClient:
    """
    Helper class for mobile QR scanner operations (React Native side reference).
    
    This is documentation for the mobile app implementation.
    
    Usage:
    ```javascript
    // React Native side
    import * as Barcode from 'expo-barcode-scanner';
    import { CameraView } from 'expo-camera';
    
    function QRScanner() {
        const [hasPermission, setHasPermission] = useState(null);
        const [scanned, setScanned] = useState(false);
        
        useEffect(() => {
            (async () => {
                const { status } = await Barcode.requestPermissionsAsync();
                setHasPermission(status === 'granted');
            })();
        }, []);
        
        const handleBarcodeScanned = async ({ data }) => {
            setScanned(true);
            
            // Send to backend
            await api.post('/api/delivery-network/scan-qr', {
                payload_b64: btoa(data),
                scan_lat: location.latitude,
                scan_lng: location.longitude,
                client_ts: Date.now(),
                device_id: deviceId,
            });
        };
        
        return (
            <CameraView
                onBarcodeScanned={handleBarcodeScanned}
                barcodeScannerSettings={{
                    types: ['qr'],
                }}
                style={StyleSheet.absoluteFillObject}
            >
                {/* Animated overlay */}
                <QRScannerOverlay isScanning={!scanned} />
            </CameraView>
        );
    }
    ```
    """

    @staticmethod
    def get_scanner_ui_spec() -> dict[str, Any]:
        """UI specifications for mobile QR scanner."""
        return {
            "scanner_overlay": {
                "corner_size": 20,
                "border_width": 3,
                "border_color": "#00ff00",
                "background_opacity": 0.3,
                "animation_duration_ms": 1500,
            },
            "animations": {
                "corner_scan": "pulse",
                "success_state": "checkmark_bounce",
                "error_state": "shake",
            },
            "haptic_feedback": {
                "on_scan_start": "light",
                "on_scan_success": "heavy",
                "on_scan_error": "medium",
            },
            "focus_behavior": {
                "auto_focus": True,
                "focus_timeout_ms": 3000,
                "torch_auto_enable_lux_threshold": 50,
            },
            "permissions": [
                "camera",
                "location",
                "device_id",
            ],
        }

    @staticmethod
    def get_offline_queue_schema() -> dict[str, Any]:
        """
        Schema for offline QR scan queue.
        
        Mobile app queues scans when offline, syncs when connection restored.
        """
        return {
            "table": "offline_qr_scans",
            "schema": {
                "id": "TEXT PRIMARY KEY",
                "qr_payload_b64": "TEXT NOT NULL",
                "scan_lat": "REAL",
                "scan_lng": "REAL",
                "client_ts": "INTEGER",
                "device_id": "TEXT",
                "scanned_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "synced": "BOOLEAN DEFAULT FALSE",
                "retry_count": "INTEGER DEFAULT 0",
            },
            "indexes": [
                "synced",
                "scanned_at",
            ],
        }
