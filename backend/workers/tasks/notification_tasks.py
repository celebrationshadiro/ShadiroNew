from __future__ import annotations

import logging
from core.database import build_mongo_manager
from email_service import send_booking_confirmation_email, send_quote_received_email

logger = logging.getLogger(__name__)


async def send_booking_confirmation_email_job(booking_id: str) -> None:
    """
    Background job to send booking confirmation email to customer.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        booking = await db.bookings.find_one({"id": booking_id})
        if not booking:
            logger.error(f"Booking {booking_id} not found for confirmation email job")
            return
            
        customer = await db.users.find_one({"id": booking["user_id"]})
        vendor = await db.vendors.find_one({"id": booking["vendor_id"]})
        
        if customer and vendor:
            email_addr = customer.get("email")
            user_name = customer.get("name") or "Valued Customer"
            vendor_name = vendor.get("business_name") or "Selected Vendor"
            amount_paise = booking.get("amount_gross_paise") or booking.get("total_amount")
            amount_rupees = float(amount_paise) / 100.0 if amount_paise else 0.0
            
            await send_booking_confirmation_email(
                to_email=email_addr,
                user_name=user_name,
                vendor_name=vendor_name,
                order_id=booking_id,
                total_amount=amount_rupees
            )
            logger.info(f"Booking confirmation email sent to {email_addr} for booking {booking_id}")
    except Exception as e:
        logger.error(f"Error in send_booking_confirmation_email_job: {e}")
    finally:
        await manager.close()


async def send_vendor_new_booking_alert(booking_id: str) -> None:
    """
    Background job to notify vendor about new booking.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        booking = await db.bookings.find_one({"id": booking_id})
        if not booking:
            return
            
        vendor = await db.vendors.find_one({"id": booking["vendor_id"]})
        if not vendor:
            return
            
        vendor_user = await db.users.find_one({"id": vendor["user_id"]})
        if vendor_user and vendor_user.get("email"):
            import resend
            from email_service import FROM_EMAIL, APP_URL
            import os
            from starlette.concurrency import run_in_threadpool
            
            resend.api_key = os.environ.get("RESEND_API_KEY", "")
            if resend.api_key:
                params = {
                    "from": FROM_EMAIL,
                    "to": [vendor_user["email"]],
                    "subject": "New Event Booking Received! - Shadiro",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1 style="color: #BE185D;">New Booking!</h1>
                        <p>Hi {vendor.get('business_name')},</p>
                        <p>You have received a new event booking order <strong>{booking_id}</strong> on Shadiro.</p>
                        <a href="{APP_URL}/vendor-dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Accept Booking</a>
                    </div>
                    """
                }
                await run_in_threadpool(resend.Emails.send, params)
                logger.info(f"Vendor new booking alert email sent to {vendor_user['email']}")
    except Exception as e:
        logger.error(f"Error in send_vendor_new_booking_alert: {e}")
    finally:
        await manager.close()


async def send_quote_accepted_notification(quote_id: str) -> None:
    """
    Background job to notify vendor that quote was accepted.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        quote = await db.quotes.find_one({"id": quote_id})
        if not quote:
            return
        vendor = await db.vendors.find_one({"id": quote["vendor_id"]})
        if not vendor:
            return
        vendor_user = await db.users.find_one({"id": vendor["user_id"]})
        if vendor_user and vendor_user.get("email"):
            import resend
            from email_service import FROM_EMAIL
            import os
            from starlette.concurrency import run_in_threadpool
            
            resend.api_key = os.environ.get("RESEND_API_KEY", "")
            if resend.api_key:
                params = {
                    "from": FROM_EMAIL,
                    "to": [vendor_user["email"]],
                    "subject": "Custom Quote Accepted by Customer! - Shadiro",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1 style="color: #BE185D;">Quote Accepted!</h1>
                        <p>Hi {vendor.get('business_name')},</p>
                        <p>Your custom quote <strong>{quote_id}</strong> has been accepted by the customer!</p>
                        <p>The booking intent is currently pending payment. We will notify you once confirmed.</p>
                    </div>
                    """
                }
                await run_in_threadpool(resend.Emails.send, params)
                logger.info(f"Quote accepted alert sent to {vendor_user['email']}")
    except Exception as e:
        logger.error(f"Error in send_quote_accepted_notification: {e}")
    finally:
        await manager.close()


async def send_payment_failure_email(customer_id: str) -> None:
    """
    Background job to notify customer about failed payment attempts.
    """
    manager = build_mongo_manager()
    await manager.connect()
    try:
        db = manager.db
        customer = await db.users.find_one({"id": customer_id})
        if customer and customer.get("email"):
            import resend
            from email_service import FROM_EMAIL, APP_URL
            import os
            from starlette.concurrency import run_in_threadpool
            
            resend.api_key = os.environ.get("RESEND_API_KEY", "")
            if resend.api_key:
                params = {
                    "from": FROM_EMAIL,
                    "to": [customer["email"]],
                    "subject": "Payment Failed - Action Required",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1 style="color: #BE185D;">Payment Failure</h1>
                        <p>Hi {customer.get('name') or 'Customer'},</p>
                        <p>Your payment attempt for your booking order on Shadiro could not be completed successfully.</p>
                        <p>Please log in to your dashboard to try paying again to hold your date range.</p>
                        <a href="{APP_URL}/dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Go to Dashboard</a>
                    </div>
                    """
                }
                await run_in_threadpool(resend.Emails.send, params)
                logger.info(f"Payment failed alert sent to {customer['email']}")
    except Exception as e:
        logger.error(f"Error in send_payment_failure_email: {e}")
    finally:
        await manager.close()
