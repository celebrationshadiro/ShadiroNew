from fastapi import APIRouter, Header, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
import hmac
import hashlib
import os
import uuid

# ── Production guard: mock endpoints are disabled in production ──
_ENV = os.getenv("APP_ENV", "development")
if _ENV == "production":
    # Provide a no-op router so imports don't break, but no routes are registered
    router = APIRouter()
else:
    router = APIRouter(prefix="/mocks", tags=["Mock Services"])

WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_secret_123")

class MockPaymentRequest(BaseModel):
    order_id: str
    amount: int

@router.post("/trigger-razorpay-webhook")
async def trigger_razorpay_webhook(req: MockPaymentRequest):
    """
    Simulates Razorpay sending a successful payment webhook to our backend.
    Used by Playwright/Cypress for E2E testing.
    """
    payload = f'{{"event":"payment.captured","payload":{{"payment":{{"entity":{{"order_id":"{req.order_id}","amount":{req.amount},"status":"captured"}}}}}}}}'
    
    # Generate fake signature
    signature = hmac.new(
        WEBHOOK_SECRET.encode(), 
        payload.encode(), 
        hashlib.sha256
    ).hexdigest()

    return {"status": "simulated", "signature_generated": signature, "payload": payload}

@router.post("/send-otp")
async def mock_send_otp(phone: str):
    """
    Bypasses real SMS gateways and returns a static OTP for testing environments.
    """
    print(f"Mock OTP sent to {phone}: 123456")
    return {"status": "success", "otp": "123456", "message": "Development mock OTP generated."}

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/send-email")
async def mock_send_email(req: EmailRequest):
    """
    Simulates Resend/SendGrid email delivery.
    """
    print(f"📩 Mock Email Sent to {req.to} | Subject: {req.subject}")
    return {"status": "success", "message_id": f"mock_msg_{uuid.uuid4().hex}"}

@router.post("/upload-image")
async def mock_cloudinary_upload(file: UploadFile = File(...)):
    """
    Simulates Cloudinary image upload, returning a static placeholder URL.
    """
    return {
        "public_id": f"mock_evt_{uuid.uuid4().hex[:8]}",
        "version": 1234567890,
        "signature": "mock_signature_abc123",
        "format": "jpg",
        "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/event_placeholder.jpg"
    }