import resend
import os
from typing import List, Optional
import logging
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")

FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")
APP_URL = os.environ.get("APP_URL", "http://localhost:3000")


async def send_welcome_email(to_email: str, user_name: str):
    """Send welcome email to new user"""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
            
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Welcome to Shadiro!",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Welcome to Shadiro, {user_name}!</h1>
                <p>We're excited to have you on board.</p>
                <p>Shadiro is your one-stop platform for planning the perfect event. Whether it's a wedding, corporate event, or birthday party, we connect you with verified vendors who can bring your vision to life.</p>
                
                <h2>What's Next?</h2>
                <ul>
                    <li>Browse our verified vendors across 9 categories</li>
                    <li>Create your first event</li>
                    <li>Request custom quotes within your budget</li>
                    <li>Book services and track your event planning journey</li>
                </ul>
                
                <a href="{APP_URL}" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Get Started</a>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">If you have any questions, feel free to reach out to our support team.</p>
            </div>
            """
        }
        
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return None


async def send_quote_received_email(to_email: str, user_name: str, vendor_name: str, quoted_price: float):
    """Notify user when they receive a quote response"""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
            
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Quote Received from {vendor_name}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">New Quote Received!</h1>
                <p>Hi {user_name},</p>
                <p><strong>{vendor_name}</strong> has responded to your quote request.</p>
                
                <div style="background-color: #f5f5f4; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h2 style="margin: 0 0 10px 0; color: #BE185D;">₹{quoted_price:,.2f}</h2>
                    <p style="margin: 0; color: #666;">Quoted Price</p>
                </div>
                
                <p>View the full quote details and accept or negotiate with the vendor.</p>
                
                <a href="{APP_URL}/dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">View Quote</a>
            </div>
            """
        }
        
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Quote received email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send quote email: {str(e)}")
        return None


async def send_booking_confirmation_email(to_email: str, user_name: str, vendor_name: str, order_id: str, total_amount: float):
    """Send booking confirmation email"""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
            
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Booking Confirmed - Shadiro",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Booking Confirmed!</h1>
                <p>Hi {user_name},</p>
                <p>Your booking with <strong>{vendor_name}</strong> has been confirmed.</p>
                
                <div style="background-color: #f5f5f4; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Order ID:</strong> {order_id}</p>
                    <p style="margin: 5px 0;"><strong>Vendor:</strong> {vendor_name}</p>
                    <p style="margin: 5px 0;"><strong>Total Amount:</strong> ₹{total_amount:,.2f}</p>
                </div>
                
                <p>The vendor will contact you soon to discuss the next steps.</p>
                
                <a href="{APP_URL}/orders/{order_id}" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">View Booking</a>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">Thank you for choosing Shadiro!</p>
            </div>
            """
        }
        
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Booking confirmation email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")
        return None


async def send_vendor_new_quote_request(to_email: str, vendor_name: str, user_name: str, services: List[str]):
    """Notify vendor about new quote request"""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
            
        services_html = "<ul>" + "".join([f"<li>{service}</li>" for service in services]) + "</ul>"
        
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "New Quote Request - Shadiro",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">New Quote Request!</h1>
                <p>Hi {vendor_name},</p>
                <p>You have received a new quote request from <strong>{user_name}</strong>.</p>
                
                <div style="background-color: #f5f5f4; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0;">Requested Services:</h3>
                    {services_html}
                </div>
                
                <p>Log in to your vendor dashboard to view details and respond to this quote request.</p>
                
                <a href="{APP_URL}/vendor-dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">View Request</a>
            </div>
            """
        }
        
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"New quote request email sent to vendor {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send vendor quote request email: {str(e)}")
        return None


async def send_vendor_registration_received(to_email: str, owner_name: str, business_name: str):
    """Notify vendor that registration was received and is under review."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None

        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Vendor Registration Received - Shadiro",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Registration Received!</h1>
                <p>Hi {owner_name},</p>
                <p>Thank you for registering <strong>{business_name}</strong> on Shadiro.</p>
                <p>Your application is under review. Our team will verify your details and you will receive an email once your vendor profile is approved.</p>
                <p>This typically takes 1-2 business days.</p>
                <a href="{APP_URL}/vendor-dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">View Dashboard</a>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">If you have any questions, contact our support team.</p>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Vendor registration received email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send vendor registration email: {str(e)}")
        return None


async def send_vendor_approval_email(to_email: str, business_name: str):
    """Notify vendor that their profile has been approved."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None

        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Your Vendor Profile is Live - {business_name}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Congratulations! You're Approved!</h1>
                <p>Great news! Your vendor profile for <strong>{business_name}</strong> has been approved.</p>
                <p>Your profile is now visible to customers on Shadiro. You can start receiving quote requests and bookings.</p>
                <a href="{APP_URL}/vendor-dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Go to Dashboard</a>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">Welcome to Shadiro!</p>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Vendor approval email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send vendor approval email: {str(e)}")
        return None


async def send_vendor_rejection_email(to_email: str, business_name: str, reason: str):
    """Notify vendor that their application was rejected."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None

        reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Update on Your Vendor Application - {business_name}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Application Update</h1>
                <p>Thank you for your interest in joining Shadiro.</p>
                <p>Unfortunately, we are unable to approve your vendor profile for <strong>{business_name}</strong> at this time.</p>
                {reason_html}
                <p>If you believe this was an error or would like to reapply with updated information, please contact our support team.</p>
                <a href="{APP_URL}" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Contact Support</a>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Vendor rejection email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send vendor rejection email: {str(e)}")
        return None


async def send_booking_cancelled_email(to_email: str, user_name: str, vendor_name: str, booking_id: str, total_amount: float, reason: str):
    """Notify user that a booking was cancelled by vendor (non-emergency)."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None

        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Booking Update - Vendor Cancellation",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Booking Update</h1>
                <p>Hi {user_name},</p>
                <p>Unfortunately, <strong>{vendor_name}</strong> cannot fulfill your booking.</p>
                <p><strong>Reason:</strong> {reason}</p>
                <div style="background-color: #f5f5f4; padding: 16px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Booking ID:</strong> {booking_id}</p>
                    <p style="margin: 5px 0;"><strong>Amount:</strong> ₹{total_amount:,.2f}</p>
                </div>
                <p>Our support team will help you find alternatives.</p>
                <a href="{APP_URL}/vendors" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Browse Vendors</a>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Booking cancelled email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send booking cancellation email: {str(e)}")
        return None


async def send_vendor_emergency_cancelled_email(to_email: str, user_name: str, vendor_name: str, booking_id: str, total_amount: float, reason: str):
    """Notify user about emergency cancellation with trust-first messaging."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None

        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Urgent: Vendor Emergency Cancellation",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">We're On It — Booking Protected</h1>
                <p>Hi {user_name},</p>
                <p><strong>{vendor_name}</strong> had an emergency and cannot fulfill your booking.</p>
                <p><strong>Reason:</strong> {reason}</p>
                <div style="background-color: #f5f5f4; padding: 16px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Booking ID:</strong> {booking_id}</p>
                    <p style="margin: 5px 0;"><strong>Amount:</strong> ₹{total_amount:,.2f}</p>
                </div>
                <p>We are already arranging a replacement vendor or processing a refund based on your preference.</p>
                <a href="{APP_URL}/dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">View Booking</a>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Emergency cancellation email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send emergency cancellation email: {str(e)}")
        return None


async def send_refund_initiated_email(to_email: str, user_name: str, amount: float):
    """Notify user that refund was initiated."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Refund Initiated - Shadiro",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Refund Initiated</h1>
                <p>Hi {user_name},</p>
                <p>Your refund has been initiated for <strong>₹{amount:,.2f}</strong>.</p>
                <p>Refunds typically take 5-7 business days to reflect in your account.</p>
                <a href="{APP_URL}/dashboard" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">View Details</a>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Refund initiated email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send refund email: {str(e)}")
        return None


async def send_emergency_admin_alert(to_email: str, vendor_name: str, booking_id: str, reason: str):
    """Notify admin about emergency cancellation."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Emergency Cancellation Alert",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Emergency Cancellation</h1>
                <p>Vendor: <strong>{vendor_name}</strong></p>
                <p>Booking ID: <strong>{booking_id}</strong></p>
                <p>Reason: {reason}</p>
                <a href="{APP_URL}/admin/emergencies" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Open Emergency Dashboard</a>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Emergency admin alert sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send admin alert email: {str(e)}")
        return None


async def send_emergency_escalation_email(to_email: str, booking_id: str, vendor_name: str, user_name: str, reason: str):
    """Notify admin team about escalation."""
    try:
        if not resend.api_key:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return None
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Emergency Escalation - Manual Review Required",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #BE185D;">Emergency Escalation</h1>
                <p>Booking ID: <strong>{booking_id}</strong></p>
                <p>Vendor: <strong>{vendor_name}</strong></p>
                <p>Customer: <strong>{user_name}</strong></p>
                <p>Reason: {reason}</p>
                <a href="{APP_URL}/admin/emergencies" style="display: inline-block; background-color: #BE185D; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 20px 0;">Open Emergency Dashboard</a>
            </div>
            """
        }
        email = await run_in_threadpool(resend.Emails.send, params)
        logger.info(f"Emergency escalation email sent to {to_email}")
        return email
    except Exception as e:
        logger.error(f"Failed to send emergency escalation email: {str(e)}")
        return None

