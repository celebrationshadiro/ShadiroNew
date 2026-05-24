# 🏗️ Admin Module - Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SHADIRO ADMIN PANEL                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────┐         ┌────────────────────────────┐   │
│  │   FRONTEND (React)       │         │    BACKEND (FastAPI)       │   │
│  │                          │         │                            │   │
│  │  ┌──────────────────┐   │         │  ┌──────────────────────┐ │   │
│  │  │  AdminLogin.js   │   │────────→│  │ /api/auth/login      │ │   │
│  │  │                  │   │         │  │ (Validate role)      │ │   │
│  │  └──────────────────┘   │         │  └──────────────────────┘ │   │
│  │           │             │         │                            │   │
│  │           ↓             │         │  ┌──────────────────────┐ │   │
│  │  ┌──────────────────┐   │         │  │ /api/admin/*         │ │   │
│  │  │  AdminLayout     │   │────────→│  │ (Protected routes)   │ │   │
│  │  │  (Sidebar Nav)   │   │         │  │                      │ │   │
│  │  └──────────────────┘   │         │  │ require_admin() ✓    │ │   │
│  │           │             │         │  └──────────────────────┘ │   │
│  │           ├─────────────┼────────→│      Admin Router       │   │
│  │           │             │         │                            │   │
│  │  Dashboard Page         │         │  ┌──────────────────────┐ │   │
│  │  Vendors Page           │         │  │ MongoDB Collections: │ │   │
│  │  Users Page             │         │  │                      │ │   │
│  │  Bookings Page          │         │  │ • users              │ │   │
│  │  Payments Page          │         │  │ • vendors            │ │   │
│  │  Audit Logs Page        │         │  │ • orders             │ │   │
│  │                          │         │  │ • payments           │ │   │
│  │  ┌──────────────────┐   │         │  │ • reviews            │ │   │
│  │  │ lib/api.js       │   │         │  │ • admin_audit_logs ✓ │ │   │
│  │  │ (Admin API Calls)│   │         │  │                      │ │   │
│  │  └──────────────────┘   │         │  └──────────────────────┘ │   │
│  │                          │         │                            │   │
│  │  ┌──────────────────┐   │         │  ┌──────────────────────┐ │   │
│  │  │ AuthContext.js   │   │         │  │ Email Service        │ │   │
│  │  │ (Token Storage)  │   │         │  │ (Resend)             │ │   │
│  │  └──────────────────┘   │         │  └──────────────────────┘ │   │
│  │                          │         │                            │   │
│  └──────────────────────────┘         │  ┌──────────────────────┐ │   │
│                                       │  │ Razorpay Integration │ │   │
│                                       │  │ (Refunds)            │ │   │
│                                       │  └──────────────────────┘ │   │
│                                       │                            │   │
│                                       └────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

### Authentication Flow
```
User Input (Email + Password)
        ↓
AdminLogin Component
        ↓
auth.login() API Call
        ↓
FastAPI: POST /api/auth/login
        ↓
Verify Credentials
        ↓
Check Role = "admin"
        ↓
If Admin: Generate JWT token
        ↓
Return token + user data
        ↓
Store in localStorage
        ↓
Update AuthContext
        ↓
Redirect to /admin
        ↓
AdminLayout checks role
        ↓
✓ AUTHENTICATED
```

### Vendor Approval Flow
```
Admin clicks Approve
        ↓
Button triggers: handleAction(vendorId, "approve")
        ↓
API Call: admin.approveVendor(vendorId, { action: "approve" })
        ↓
Request to: PUT /api/admin/vendors/{vendorId}/approve
        ↓
Backend: require_admin checks JWT
        ↓
Verify vendor exists
        ↓
Update vendor status to "APPROVED"
        ↓
Log admin action in admin_audit_logs
        ↓
Send approval email via Resend
        ↓
Return success response
        ↓
Frontend: Load vendors, show success toast
        ↓
Display updated vendor with green badge
        ↓
✓ COMPLETE
```

### Payment Refund Flow
```
Admin finds payment
        ↓
Clicks "Refund" button
        ↓
Enters refund reason
        ↓
Submits: admin.refundPayment(paymentId, reason)
        ↓
Request: POST /api/admin/payments/{paymentId}/refund
        ↓
Backend validates:
  - Payment exists
  - Status = "success"
  - Has razorpay_payment_id
        ↓
Call Razorpay API: payment.refund()
        ↓
Update payment status to "refunded"
        ↓
Store refund_id and reason
        ↓
Log action in admin_audit_logs
        ↓
Return refund confirmation
        ↓
Frontend updates UI
        ↓
Show success message
        ↓
✓ REFUND PROCESSED
```

---

## State Management Architecture

### AuthContext (React)
```
AuthContext State:
├── user (Profile data)
├── token (JWT)
├── loading (Boolean)
└── isAuthenticated (Boolean)

AuthContext Methods:
├── login(email, password) → async
├── logout() → clear all
├── loginWithToken(token, userData) → direct set
└── register(data) → async
```

### Component State Examples

#### AdminVendors Component
```
State:
├── vendors[] - List of vendors
├── loading - Fetch status
├── filter - Current status filter
├── actioningId - Button loading ID
├── selectedVendor - For stats popup
├── vendorStats - Stats data
├── showReasonDialog - Modal visibility
└── reasonInput - User reason text
```

#### AdminUsers Component
```
State:
├── users[] - List of users
├── loading - Fetch status
├── search - Search query
├── roleFilter - Selected role
├── activeFilter - Active/Blocked filter
├── blockingId - Button loading ID
└── activatingId - Button loading ID
```

---

## API Endpoint Hierarchy

```
/api/
├── /auth/
│   ├── POST /register
│   ├── POST /login
│   └── GET /me
│
└── /admin/
    ├── GET /analytics ────────────────→ AdminDashboard
    │
    ├── /users
    │   ├── GET ──────────────────────→ AdminUsers (list)
    │   ├── PUT /{id}/block ───────────→ AdminUsers (block)
    │   └── PUT /{id}/activate ──────→ AdminUsers (activate)
    │
    ├── /vendors
    │   ├── GET ──────────────────────→ AdminVendors (list)
    │   ├── PUT /{id}/approve ───────→ AdminVendors (actions)
    │   ├── PUT /{id}/featured ─────→ AdminVendors (featured)
    │   └── GET /{id}/stats ────────→ AdminVendors (stats popup)
    │
    ├── /bookings
    │   └── GET ──────────────────────→ AdminBookings (list)
    │
    ├── /payments
    │   ├── GET ──────────────────────→ AdminPayments (list)
    │   └── POST /{id}/refund ──────→ AdminPayments (refund)
    │
    └── /audit-logs
        └── GET ──────────────────────→ AdminAuditLogs (list)
```

---

## Database Schema Overview

### admin_audit_logs Collection
```
{
  "_id": ObjectId,
  "id": UUID,
  "admin_id": "user_id",           // Who did it
  "action_type": "vendor_approve",  // What happened
  "target_type": "vendor",          // What entity
  "target_id": "vendor_id",         // Which entity
  "details": {                      // Additional info
    "vendor_name": "Wedding Pro"
  },
  "reason": "Request for more docs", // Why
  "created_at": "2026-02-10T...",   // When
  "ip_address": "192.168.1.100",    // Where from
  "success": true                    // Did it work
}
```

### Enhanced users Collection
```
{
  "id": UUID,
  "email": "admin@example.com",
  "name": "John Admin",
  "role": "admin",          // ← Key field
  "hashed_password": "...",
  "is_active": true,        // ← For blocking
  "created_at": "2026-01...",
  "blocked_at": null,       // ← When blocked
  "block_reason": null      // ← Why blocked
}
```

### Enhanced vendors Collection
```
{
  "id": UUID,
  "business_name": "Wedding Services",
  "user_id": "vendor_user_id",
  "status": "approved",        // pending|approved|rejected|suspended
  "is_featured": true,         // ← Featured toggle
  "is_active": true,
  "created_at": "2026-01...",
  "approved_at": "2026-02...", // ← When approved
  "suspension_reason": null    // ← If suspended
}
```

---

## Security Layers

### Layer 1: Authentication
```
HTTP Request with Bearer Token
        ↓
FastAPI extracts token from Authorization header
        ↓
Validate JWT signature
        ↓
Check token expiration
        ↓
Extract payload (user_id, role, etc)
        ↓
✓ Token Valid or ✗ 401 Unauthorized
```

### Layer 2: Authorization (RBAC)
```
Endpoint requires admin role
        ↓
Check: current_user.get("role") == "admin"
        ↓
NOT admin: ✗ 403 Forbidden
        ↓
IS admin: ✓ Continue to handler
```

### Layer 3: Audit Logging
```
Admin action executed
        ↓
Extract: admin_id, action_type, target_id
        ↓
Capture: IP address, timestamp, reason
        ↓
Record success/failure
        ↓
Store in admin_audit_logs
        ↓
Immutable historical record
```

### Layer 4: Data Validation
```
Input received
        ↓
Validate with Pydantic models
        ↓
Invalid: ✗ 422 Unprocessable Entity
        ↓
Valid: ✓ Process request
        ↓
Validate business logic (vendor exists, etc)
        ↓
Invalid: ✗ 404/400 Error
        ↓
Valid: ✓ Execute action
```

---

## Component Dependency Tree

```
App.js (Root)
├── BrowserRouter
├── AuthProvider (Context)
└── AppContent
    ├── Navbar (non-admin only)
    ├── Routes
    │   ├── / → HomePage
    │   ├── /vendors → VendorListPage
    │   ├── /auth → AuthPage
    │   ├── /admin/login → AdminLogin
    │   └── /admin → AdminLayout
    │       └── AdminLayout (Protected by role check)
    │           ├── Sidebar Navigation
    │           └── Outlet (Nested Routes)
    │               ├── AdminDashboard
    │               ├── AdminVendors
    │               │   └── Stats popup (child)
    │               │   └── Reason modals (child)
    │               ├── AdminUsers
    │               ├── AdminBookings
    │               ├── AdminPayments
    │               └── AdminAuditLogs
    └── Footer (non-admin only)
```

---

## Error Handling Flow

```
API Call in Frontend Component
        ↓
try/catch block
        ↓
Success:
  ├── Update UI state
  ├── Show success toast
  └── Refetch data if needed
        ↓
Error:
  ├── Extract error message
  ├── Show error toast
  ├── Log to console
  └── Optionally retry
        ↓
Finally:
  └── Set loading to false
```

---

## Performance Optimizations

### Frontend
```
✓ Lazy loading (React.lazy) for admin pages
✓ Pagination on all lists (limit 50-100)
✓ Debounced search inputs
✓ useEffect cleanup for subscriptions
✓ Memoized components (useMemo, useCallback)
```

### Backend
```
✓ Async/await for I/O operations
✓ Index database queries for filters
✓ Pagination (skip/limit) for large datasets
✓ Async email delivery (non-blocking)
✓ Connection pooling with MongoDB
```

---

## Scalability Considerations

### Current Implementation
```
Single Admin Instance:
├── One admin panel
├── Multiple admins (same instance)
├── Load balanced API backend
├── Centralized MongoDB
└── Single email service (Resend)
```

### Future Scaling Options
```
Multi-Region:
├── Admin panel in each region
├── Regional databases (with sync)
├── Regional email services
└── CDN for static assets

High Availability:
├── Admin panel replicas
├── Database replication
├── Failover mechanism
├── Audit log backup
└── Rate limiting on admin APIs
```

---

## Integration Points

### External Services
```
1. MongoDB
   ├── Store: users, vendors, orders, payments
   ├── Store: admin_audit_logs (NEW)
   └── Indexed queries for performance

2. Razorpay
   ├── Payment creation (existing)
   ├── Payment verification (existing)
   └── Refund processing (NEW)

3. Resend (Email)
   ├── Welcome emails (existing)
   ├── Quote notifications (existing)
   ├── Vendor approval email (NEW)
   └── Vendor rejection email (NEW)

4. Socket.IO (Optional)
   ├── Real-time notifications
   └── Live admin activity updates
```

---

## Monitoring & Logging

### Application Logs
```
FastAPI Logger:
├── INFO: Admin login, vendor approval, refunds
├── ERROR: Failed operations, exceptions
└── DEBUG: Request details, auth checks

React Console:
├── API calls and responses
├── State changes
├── Event handlers
└── Error details
```

### Metrics to Track
```
✓ Admin login count
✓ Vendor approvals/rejections per day
✓ Average approval time
✓ User block rate
✓ Payment refund rate
✓ System errors
✓ Response times
✓ Admin activity heatmap
```

---

## Testing Strategy

### Unit Tests
```
Backend:
├── Authentication (JWT validation)
├── Authorization (role checking)
└── Audit logging (format validation)

Frontend:
├── Component rendering
├── Form submission
├── Error handling
└── State management
```

### Integration Tests
```
E2E Flows:
├── Admin login → Dashboard
├── Vendor approval → Email sent → Audit log
├── User block → Status change → Audit log
└── Payment refund → Status update → Audit log
```

### Security Tests
```
✓ SQL injection attempts
✓ JWT tampering
✓ Missing role checks
✓ Unauthorized access
✓ Data exposure
```

---

**Architecture Documentation Complete ✅**

*For implementation details, see: ADMIN_MODULE_GUIDE.md*
*For quick reference, see: ADMIN_QUICK_REFERENCE.md*
