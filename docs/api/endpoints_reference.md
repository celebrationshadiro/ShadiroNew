# API Endpoints Reference - Frontend Requirements

This document lists all API endpoints required by the newly implemented frontend components.

## 📋 Quick Reference

**Base URL**: `${process.env.REACT_APP_API_URL}`  
**WebSocket URL**: `${process.env.REACT_APP_WS_URL}`  
**Auth Header**: `Authorization: Bearer {token}`

---

## 🔔 Notification Endpoints

### 1. Send Email Notification
```http
POST /api/notifications/email
Content-Type: application/json
Authorization: Bearer {token}

{
  "recipient_id": "user_uuid",
  "subject": "Booking Confirmed",
  "message": "Your booking has been confirmed",
  "type": "booking_confirmed",
  "booking_id": "booking_uuid",
  "priority": "normal"
}

Response (200 OK):
{
  "id": "notification_uuid",
  "status": "sent",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Send SMS Notification
```http
POST /api/notifications/sms
Content-Type: application/json
Authorization: Bearer {token}

{
  "phone_number": "+91xxxxxxxxxx",
  "message": "Your booking confirmed. Booking ID: BK123456",
  "type": "booking_confirmed",
  "priority": "high"
}

Response (200 OK):
{
  "id": "notification_uuid",
  "status": "sent",
  "delivery_time": "2024-01-01T12:00:05Z"
}
```

### 3. Send Push Notification
```http
POST /api/notifications/push
Content-Type: application/json
Authorization: Bearer {token}

{
  "user_id": "user_uuid",
  "title": "Booking Confirmed",
  "message": "Your event booking has been confirmed",
  "notification_id": "booking_uuid",
  "type": "booking_confirmed",
  "priority": "high",
  "icon": "📅",
  "action_url": "/bookings/BK123456"
}

Response (200 OK):
{
  "id": "push_uuid",
  "status": "queued",
  "scheduled_push_count": 1
}
```

### 4. Get Notifications List
```http
GET /api/notifications?type=booking&read=false&limit=20
Authorization: Bearer {token}

Query Parameters:
- type: Optional (all, booking, payment, message, vendor, system)
- read: Optional (true, false)
- limit: Optional (default 20)
- offset: Optional (default 0)

Response (200 OK):
{
  "notifications": [
    {
      "id": "notif_uuid",
      "type": "booking_confirmed",
      "title": "Booking Confirmed",
      "message": "Your event service is confirmed",
      "read": false,
      "priority": "normal",
      "created_at": "2024-01-01T12:00:00Z",
      "action_url": "/bookings/BK123456"
    }
  ],
  "total_count": 5,
  "unread_count": 2
}
```

### 5. Bulk Delete Notifications
```http
POST /api/notifications/bulk-delete
Content-Type: application/json
Authorization: Bearer {token}

{
  "notification_ids": [
    "notif_uuid_1",
    "notif_uuid_2"
  ]
}

Response (200 OK):
{
  "deleted_count": 2,
  "remaining_count": 3
}
```

### 6. WebSocket - Real-time Notifications
```
ws://api.example.com/ws/notifications/{user_id}
Headers: Authorization: Bearer {token}

Connection Flow:
1. Connect to WebSocket
2. Server expects token in header
3. Server sends any pending notifications
4. Client receives new notifications in real-time

Receive Message Format:
{
  "type": "notification",
  "id": "notif_uuid",
  "notification_type": "booking_confirmed",
  "title": "Booking Confirmed",
  "message": "Your booking has been confirmed",
  "data": {
    "booking_id": "BK123456",
    "vendor_name": "John's Events"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 📅 Booking Endpoints

### 1. Create Booking
```http
POST /api/bookings
Content-Type: application/json
Authorization: Bearer {token}

{
  "vendor_id": "vendor_uuid",
  "service_id": "service_uuid",
  "quantity": 2,
  "total_amount": 12360,
  "gst_amount": 2160,
  "delivery_fee": 200,
  "payment_method": "UPI",
  "event_date": "2024-02-15",
  "event_time": "18:00",
  "location": "123 Main St, City",
  "people_count": 50,
  "special_requests": "Please bring chiller units"
}

Response (201 Created):
{
  "id": "booking_uuid",
  "booking_id": "BK123456",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z",
  "payment_status": "pending",
  "total_amount": 12360
}
```

### 2. Accept Booking (Vendor)
```http
POST /api/bookings/{booking_id}/accept
Authorization: Bearer {token}

Response (200 OK):
{
  "id": "booking_uuid",
  "status": "confirmed",
  "vendor_response_time": 45,
  "confirmed_at": "2024-01-01T12:45:00Z"
}
```

### 3. Reject Booking (Vendor)
```http
POST /api/bookings/{booking_id}/reject
Content-Type: application/json
Authorization: Bearer {token}

{
  "rejection_reason": "Fully booked on this date",
  "offered_date": null
}

Response (200 OK):
{
  "id": "booking_uuid",
  "status": "rejected",
  "rejected_at": "2024-01-01T12:45:00Z",
  "reason": "Fully booked on this date"
}
```

### 4. Cancel Booking (Vendor Emergency)
```http
POST /api/bookings/{booking_id}/cancel
Content-Type: application/json
Authorization: Bearer {token}

{
  "cancellation_reason": "Equipment malfunction",
  "refund_method": "original_payment_method"
}

Response (200 OK):
{
  "id": "booking_uuid",
  "status": "cancelled",
  "cancelled_at": "2024-01-01T12:45:00Z",
  "reason": "Equipment malfunction",
  "incident_logged": true,
  "incident_id": "incident_123"
}
```

### 5. Get Vendor Bookings
```http
GET /api/vendor/bookings?status=pending&limit=10
Authorization: Bearer {token}

Query Parameters:
- status: Optional (pending, confirmed, completed, cancelled, rejected)
- limit: Optional (default 10)
- offset: Optional (default 0)

Response (200 OK):
{
  "bookings": [
    {
      "id": "booking_uuid",
      "booking_id": "BK123456",
      "customer_name": "Jane Doe",
      "service_name": "Photography",
      "total_amount": 12360,
      "event_date": "2024-02-15",
      "status": "pending",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total_count": 5,
  "pending_count": 2
}
```

### 6. Get Vendor Dashboard Data
```http
GET /api/vendor/dashboard
Authorization: Bearer {token}

Response (200 OK):
{
  "stats": {
    "total_revenue": 125000,
    "active_bookings": 8,
    "pending_quotes": 3,
    "average_rating": 4.8
  },
  "recent_bookings": [...],
  "recent_quotes": [...]
}
```

---

## 💬 Chat Endpoints

### 1. Fetch Chat Messages
```http
GET /api/messages/{booking_id}?limit=50
Authorization: Bearer {token}

Query Parameters:
- limit: Optional (default 50)
- offset: Optional (default 0)

Response (200 OK):
{
  "messages": [
    {
      "id": "message_uuid",
      "booking_id": "booking_uuid",
      "sender_id": "user_uuid",
      "sender_name": "John Doe",
      "content": "Can you provide quotes?",
      "message_type": "text",
      "read": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total_count": 15
}
```

### 2. Send Message
```http
POST /api/messages/send
Content-Type: application/json
Authorization: Bearer {token}

{
  "booking_id": "booking_uuid",
  "recipient_id": "recipient_uuid",
  "content": "Can you come by 6 PM?",
  "message_type": "text"
}

Response (201 Created):
{
  "id": "message_uuid",
  "sender_id": "user_uuid",
  "sender_name": "Jane Doe",
  "content": "Can you come by 6 PM?",
  "created_at": "2024-01-01T12:00:00Z",
  "read": false
}
```

### 3. WebSocket - Real-time Chat
```
ws://api.example.com/ws/chat/{booking_id}
Headers: Authorization: Bearer {token}

Connection Flow:
1. Connect to WebSocket for specific booking
2. Send messages via WebSocket
3. Receive messages in real-time

Receive Message Format:
{
  "type": "message",
  "id": "message_uuid",
  "sender_id": "user_uuid",
  "sender_name": "John Doe",
  "content": "I'll be there!",
  "timestamp": "2024-01-01T12:00:00Z"
}

Typing Indicator:
{
  "type": "typing",
  "user_id": "user_uuid",
  "user_name": "Jane"
}
```

---

## 🧾 Quote Endpoints

### 1. Create Quote (supports attachments)
```http
POST /api/quotes
Content-Type: application/json
Authorization: Bearer {token}

{
  "event_id": "event_uuid",
  "vendor_id": "vendor_uuid",
  "user_id": "user_uuid",
  "requested_services": ["Photography", "Candid"],
  "message": "Need coverage for 8 hours.",
  "attachments": [
    { "url": "https://cdn.example.com/quote/ref1.pdf", "filename": "ref1.pdf" }
  ]
}
```

### 2. Upload Quote Attachment
```http
POST /api/quotes/attachments
Content-Type: multipart/form-data
Authorization: Bearer {token}

file=@/path/to/reference.pdf

Response (200 OK):
{
  "url": "https://res.cloudinary.com/.../reference.pdf",
  "filename": "reference.pdf",
  "content_type": "application/pdf",
  "size": 12456
}
```

Note: Multi-event quote requests are handled by sending multiple `POST /api/quotes` calls (one per event).
Quote responses returned to vendors may include lead scoring fields:
```
lead_score: number (0-100)
lead_score_label: "Hot" | "Warm" | "Cold"
lead_score_reasons: string[]
```

---

## 🤖 Assistant & Onboarding Endpoints

### 1. Assistant Message
```http
POST /api/assistant/message
Content-Type: application/json

{
  "message": "Help me complete onboarding",
  "role": "vendor",
  "language": "en",
  "category_id": "grocery",
  "profile": {
    "business_name": "Fresh Mart",
    "city": "Mumbai"
  }
}

Response (200 OK):
{
  "reply": "To complete onboarding...",
  "suggestions": ["Show required fields checklist"],
  "actions": [{"type": "open_onboarding"}],
  "provider": "rules",
  "confidence": 0.82,
  "metadata": {
    "onboarding": {
      "missing_required": ["product_catalog"]
    }
  }
}
```

### 2. AI Quote Draft (Copilot)
```http
POST /api/assistant/quote/draft
Content-Type: application/json
Authorization: Bearer {token}

{
  "quote_id": "quote_uuid",
  "tone": "formal",
  "requested_services": ["DJ", "Lighting"]
}

Response (200 OK):
{
  "draft": "Thank you for considering us...",
  "reasoning": "Draft highlights coverage...",
  "upsells": ["Lighting rig", "After-party hour"],
  "suggested_price": 25000,
  "provider": "rules",
  "ai_enabled": false,
  "confidence": 0.78,
  "metadata": {
    "llm_provider": "rules"
  }
}
```

### 3. Negotiation Summary (Copilot)
```http
POST /api/assistant/negotiation/summary
Content-Type: application/json
Authorization: Bearer {token}

{
  "chat_id": "user_vendor_chat_id"
}

Response (200 OK):
{
  "summary": "Conversation has 6 messages...",
  "key_points": ["Budget discussed", "Date/timing discussed"],
  "next_steps": ["Confirm availability", "Share final quote options"],
  "provider": "rules",
  "ai_enabled": false,
  "confidence": 0.75,
  "metadata": {
    "llm_provider": "rules"
  }
}
```

### 4. Reply Suggestions (Copilot)
```http
POST /api/assistant/reply/suggest
Content-Type: application/json
Authorization: Bearer {token}

{
  "chat_id": "user_vendor_chat_id",
  "tone": "quick"
}

Response (200 OK):
{
  "suggestions": [
    "Got it. Send details and we will confirm."
  ],
  "tone": "quick",
  "provider": "rules",
  "ai_enabled": false,
  "confidence": 0.7,
  "metadata": {
    "llm_provider": "rules"
  }
}
```

### 5. Onboarding Requirements
```http
GET /api/assistant/onboarding/requirements/{category_id}

Response (200 OK):
{
  "category": "grocery",
  "label": "Grocery Vendors",
  "required": ["delivery_radius", "product_catalog"],
  "recommended": ["quality_grade"]
}
```

### 6. Onboarding Validation
```http
POST /api/assistant/onboarding/validate
Content-Type: application/json

{
  "category_id": "grocery",
  "business_name": "Fresh Mart",
  "product_catalog": [
    { "name": "Rice", "unit": "kg", "unit_price": 80 }
  ]
}
```

### 7. Update Vendor Onboarding
```http
PUT /api/vendors/{vendor_id}/onboarding
Content-Type: application/json
Authorization: Bearer {token}

{
  "business_name": "Fresh Mart",
  "grocery_items": [
    { "name": "Rice", "unit": "kg", "unit_price": 80, "availability": "in_stock" }
  ],
  "caterer_menu_items": [
    { "name": "Paneer Tikka", "category": "appetizers", "unit_price": 250 }
  ]
}

Response (200 OK):
{
  "vendor": { "...": "..." },
  "onboarding": {
    "status": "complete",
    "missing_required": []
  }
}
```

---

## Pricing Endpoints

### 1. Pricing Preview (Quote Preview)
```http
POST /api/pricing/preview
Content-Type: application/json
Authorization: Bearer {token}

{
  "vendor_id": "vendor_uuid",
  "event_date": "2026-02-14",
  "base_amount": 20000
}

Response (200 OK):
{
  "vendor_id": "vendor_uuid",
  "base_amount": 20000,
  "multiplier": 1.2,
  "flat_fee": 500,
  "total": 24500,
  "applied_rules": [
    {
      "id": "rule_1",
      "label": "Weekend uplift",
      "multiplier": 1.2,
      "flat_fee": 500
    }
  ]
}
```

### 2. Update Vendor Pricing Rules
```http
PUT /api/vendors/{vendor_id}/pricing-rules
Content-Type: application/json
Authorization: Bearer {token}

[
  {
    "label": "Weekend uplift",
    "days_of_week": ["sat", "sun"],
    "multiplier": 1.15,
    "flat_fee": 0
  }
]
```

---
## 🛠️ Admin Endpoints
### 5. Pricing Insights
```http
GET /api/admin/pricing/insights
Authorization: Bearer {token}

Response (200 OK):
{
  "avg_base_price": 18000,
  "vendors_with_pricing_rules": 12,
  "total_vendors": 120,
  "category_rule_coverage": {
    "dj": 4,
    "caterer": 3
  }
}
```

### 1. Get Incident List (Urgent Cancellations)
```http
GET /api/admin/incidents?status=active&limit=20
Authorization: Bearer {token}

Query Parameters:
- status: Optional (active, resolved, pending)
- limit: Optional (default 20)
- offset: Optional (default 0)

Response (200 OK):
{
  "incidents": [
    {
      "id": "incident_uuid",
      "booking_id": "booking_uuid",
      "vendor_id": "vendor_uuid",
      "vendor_name": "John's Events",
      "customer_name": "Jane Doe",
      "service_name": "Photography",
      "amount": 12360,
      "cancellation_reason": "Equipment failure",
      "incident_timestamp": "2024-01-01T12:00:00Z",
      "time_since_incident": "5 minutes"
    }
  ],
  "total_count": 3
}
```

### 2. Get Suggested Replacement Vendors
```http
GET /api/admin/incidents/{incident_id}/suggested-vendors?limit=4
Authorization: Bearer {token}

Query Parameters:
- limit: Optional (default 4)

Response (200 OK):
{
  "suggested_vendors": [
    {
      "id": "vendor_uuid",
      "name": "Premium Events Co",
      "rating": 4.9,
      "completion_rate": 99,
      "available": true,
      "distance": "2.5 km",
      "ai_rank": 1,
      "reason": "Perfect match - same service, excellent rating"
    }
  ]
}
```

### 3. Assign Replacement Vendor
```http
POST /api/admin/incidents/{incident_id}/assign-replacement
Content-Type: application/json
Authorization: Bearer {token}

{
  "replacement_vendor_id": "vendor_uuid",
  "refund_method": "wallet",
  "incentive_percentage": 5
}

Response (200 OK):
{
  "id": "replacement_uuid",
  "original_booking_id": "booking_uuid",
  "replacement_vendor_id": "vendor_uuid",
  "status": "assigned",
  "assigned_at": "2024-01-01T12:45:00Z",
  "notification_sent": true
}
```

### 4. Get Admin Analytics
```http
GET /api/admin/analytics?period=week
Authorization: Bearer {token}

Query Parameters:
- period: Optional (day, week, month, year)

Response (200 OK):
{
  "analytics": {
    "cancellation_rate": 2.5,
    "avg_resolution_time": 45,
    "success_rate": 98.5,
    "total_incidents_today": 3,
    "incidents_resolved": 2
  },
  "time_series": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "incidents": 5,
      "resolved": 4
    }
  ]
}
```

---

## 👥 User Profile Endpoints (Existing)

### Get User Profile
```http
GET /api/users/profile
Authorization: Bearer {token}

Response (200 OK):
{
  "id": "user_uuid",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+91xxxxxxxxxx",
  "role": "customer",
  "avatar": "https://..."
}
```

### Get Vendor Profile
```http
GET /api/vendor/profile
Authorization: Bearer {token}

Response (200 OK):
{
  "id": "vendor_uuid",
  "name": "John's Events",
  "email": "john@example.com",
  "rating": 4.8,
  "total_reviews": 125,
  "services": [...],
  "package_count": 5,
  "response_time": "< 2 hours"
}
```

---

## 🔐 Authentication (Existing)

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response (200 OK):
{
  "token": "eyJhbGc...",
  "user": {
    "id": "user_uuid",
    "name": "Jane Doe",
    "role": "customer"
  }
}
```

---

## 📝 Error Responses

All endpoints return standardized error responses:

```http
400 Bad Request:
{
  "error": "Invalid booking amount",
  "code": "INVALID_AMOUNT",
  "details": "Amount must be greater than 0"
}

401 Unauthorized:
{
  "error": "Invalid or expired token",
  "code": "INVALID_TOKEN"
}

403 Forbidden:
{
  "error": "You don't have permission to access this resource",
  "code": "PERMISSION_DENIED"
}

404 Not Found:
{
  "error": "Booking not found",
  "code": "NOT_FOUND"
}

500 Internal Server Error:
{
  "error": "Internal server error",
  "code": "INTERNAL_ERROR",
  "request_id": "req_123456"
}
```

---

## 🔄 Pagination

All list endpoints support pagination:

```
Query Parameters:
- limit: Number of items (default 20, max 100)
- offset: Starting position (default 0)

Response Format:
{
  "data": [...],
  "total_count": 150,
  "limit": 20,
  "offset": 0,
  "has_next": true,
  "has_previous": false
}
```

---

## 📌 Environment Variables Required

```bash
# Frontend
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000

# Optional
REACT_APP_ENVIRONMENT=development
REACT_APP_LOG_LEVEL=debug
```

---

## ✅ Implementation Checklist for Backend

- [ ] Send Email Notification endpoint
- [ ] Send SMS Notification endpoint
- [ ] Send Push Notification endpoint
- [ ] Get Notifications List endpoint
- [ ] Bulk Delete Notifications endpoint
- [ ] WebSocket /ws/notifications/{user_id}
- [ ] Create Booking endpoint
- [ ] Accept Booking endpoint
- [ ] Reject Booking endpoint
- [ ] Cancel Booking endpoint
- [ ] Get Vendor Bookings endpoint
- [ ] Get Vendor Dashboard endpoint
- [ ] Fetch Chat Messages endpoint
- [ ] Send Message endpoint
- [ ] WebSocket /ws/chat/{booking_id}
- [ ] Get Admin Incidents endpoint
- [ ] Get Suggested Vendors endpoint
- [ ] Assign Replacement Vendor endpoint
- [ ] Get Admin Analytics endpoint

---

## 🧪 Testing Curl Examples

### Create Booking
```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "vendor_123",
    "service_id": "service_123",
    "quantity": 2,
    "total_amount": 12360,
    "gst_amount": 2160,
    "delivery_fee": 200,
    "payment_method": "UPI",
    "event_date": "2024-02-15",
    "location": "123 Main St"
  }'
```

### Send Notification
```bash
curl -X POST http://localhost:8000/api/notifications/email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "user_123",
    "subject": "Booking Confirmed",
    "message": "Your booking has been confirmed",
    "type": "booking_confirmed",
    "priority": "normal"
  }'
```

---

**Last Updated**: Phase 3 Implementation  
**API Version**: v1  
**Status**: Ready for Backend Implementation


