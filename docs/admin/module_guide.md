# 🔐 Shadiro Platform – Admin Module (Phase 3) Implementation Guide

## Overview

The Admin Module for Shadiro Platform provides complete administrative control over the event services platform. This module includes centralized platform control, analytics dashboards, vendor management, user moderation, payment handling, and comprehensive audit logging.

---

## ✅ Completed Features

### Backend (FastAPI)
- ✅ **Admin Authentication & Security**
  - Role-based access control (RBAC) with "admin" role
  - JWT token includes role information
  - `require_admin` dependency for route protection

- ✅ **Admin Analytics Endpoint** (`GET /api/admin/analytics`)
  - Total users and vendors count
  - Pending vendor approvals
  - Total revenue from confirmed orders
  - Monthly bookings trend (last 6 months)
  - Category-wise demand

- ✅ **User Management** 
  - `GET /api/admin/users` - List all users with filters
  - `PUT /api/admin/users/{user_id}/block` - Block user account with reason
  - `PUT /api/admin/users/{user_id}/activate` - Reactivate blocked user
  - Search by name/email, filter by role, filter by active status

- ✅ **Vendor Management**
  - `GET /api/admin/vendors` - List all vendors with status/category filters
  - `PUT /api/admin/vendors/{vendor_id}/approve` - Approve vendor
  - `PUT /api/admin/vendors/{vendor_id}/approve` - Reject vendor (with reason)
  - `PUT /api/admin/vendors/{vendor_id}/approve` - Suspend vendor (with reason)
  - `PUT /api/admin/vendors/{vendor_id}/featured` - Toggle featured status
  - `GET /api/admin/vendors/{vendor_id}/stats` - Get detailed vendor statistics

- ✅ **Bookings & Payments**
  - `GET /api/admin/bookings` - List all orders with status filter
  - `GET /api/admin/payments` - List all payments with status tracking
  - `POST /api/admin/payments/{payment_id}/refund` - Process refunds via Razorpay

- ✅ **Audit Logging**
  - `GET /api/admin/audit-logs` - Comprehensive audit trail
  - AdminAuditLog model for tracking all admin actions
  - Logs include: admin_id, action_type, target_type, target_id, reason, timestamp, IP address, success status

- ✅ **Email Notifications**
  - Vendor approval email with dashboard link
  - Vendor rejection email with reason
  - Async email delivery via Resend

---

### Frontend (React)

- ✅ **Admin Login Page** (`/admin/login`)
  - Secure email + password authentication
  - Role validation (admin-only access)
  - Secure token storage in localStorage
  - Automatic redirect to admin dashboard

- ✅ **Admin Dashboard** (`/admin`)
  - Key metrics cards:
    - Total Users
    - Total Vendors
    - Pending Approvals
    - Total Revenue
  - Charts & trends:
    - Monthly bookings overview
    - Category demand distribution

- ✅ **Admin User Management** (`/admin/users`)
  - View all users with detailed information
  - Search by name or email
  - Filter by role (Admin/Vendor/User)
  - Filter by status (Active/Blocked)
  - Block user accounts with reason
  - Activate blocked users
  - Real-time statistics (total, by role, blocked count)

- ✅ **Admin Vendor Management** (`/admin/vendors`)
  - View all vendors with status badges
  - Filter by approval status (All/Pending/Approved/Rejected/Suspended)
  - Approve pending vendors
  - Reject vendors with modal dialog for reason
  - Suspend approved vendors with modal dialog for reason
  - View vendor statistics (bookings, revenue, ratings)
  - Toggle featured status with single click
  - Quick action buttons with loading states

- ✅ **Admin Bookings** (`/admin/bookings`)
  - View all orders/bookings
  - Filter by status
  - See booking details, amounts, and services
  - Track booking lifecycle

- ✅ **Admin Payments** (`/admin/payments`)
  - View complete payment history
  - Statistics cards:
    - Successful payments count
    - Total revenue
    - Failed payments count
    - Refunded amount
  - Process refunds with reason
  - View Razorpay order references
  - Track refund history with refund IDs

- ✅ **Admin Audit Logs** (`/admin/audit-logs`)
  - Complete audit trail of all admin actions
  - Filters for admin_id, action_type, target_type
  - Color-coded action badges
  - Detailed information:
    - Admin who performed action
    - Target entity and ID
    - Reason/comment
    - IP address
    - Timestamp
  - Pagination support

---

## 📁 Project Structure

### Backend Structure
```
backend/
├── models.py                    # Data models including AdminAuditLog & AdminActionType
├── auth.py                      # Authentication & RBAC (require_role, require_admin)
├── server.py                    # Main FastAPI app
├── routers/
│   └── admin.py                 # Complete admin router with all endpoints
├── email_service.py            # Email notifications (approval/rejection)
└── chat_service.py             # Socket.IO integration
```

### Frontend Structure
```
frontend/src/
├── pages/admin/
│   ├── AdminLogin.js            # Secure admin login
│   ├── AdminLayout.js           # Layout with sidebar navigation
│   ├── AdminDashboard.js        # Analytics dashboard
│   ├── AdminUsers.js            # User management
│   ├── AdminVendors.js          # Vendor management
│   ├── AdminBookings.js         # Bookings overview
│   ├── AdminPayments.js         # Payment management
│   └── AdminAuditLogs.js        # Audit trail viewer
├── components/
│   └── AdminRoute.js            # Optional protected route wrapper
├── lib/
│   └── api.js                   # Admin API service methods
├── contexts/
│   └── AuthContext.js           # Authentication context with logout
└── App.js                       # Routes including admin paths
```

---

## 🚀 Quick Start

### 1. Admin User Creation
To create an admin user for testing:

```python
# Register a normal user first via POST /api/auth/register
# Then manually update their role in MongoDB:
db.users.update_one(
    {"email": "admin@shadiro.com"},
    {"$set": {"role": "admin"}}
)
```

### 2. Access Admin Panel
1. Navigate to `/admin/login`
2. Enter admin credentials
3. Dashboard loads with all metrics
4. Navigate through sidebar: Dashboard → Vendors → Users → Bookings → Payments → Audit Logs

### 3. Key Admin Operations

#### Approve a Vendor
1. Go to `/admin/vendors`
2. Filter by "pending"
3. Click Approve button
4. Vendor receives approval email
5. Action logged in audit trail

#### Block a User
1. Go to `/admin/users`
2. Search/filter to find user
3. Click Block button
4. Enter block reason
5. User account deactivated

#### Process a Refund
1. Go to `/admin/payments`
2. Find successful payment
3. Click Refund button
4. Enter refund reason
5. Refund processed via Razorpay
6. Payment status updates to "refunded"

---

## 🔑 API Endpoints Reference

### Analytics
```
GET /api/admin/analytics
├── total_users: int
├── total_vendors: int
├── pending_vendor_approvals: int
├── total_revenue: float
├── monthly_bookings: [{month, count}]
└── category_demand: [{category, count}]
```

### Users
```
GET /api/admin/users?search=&role=&limit=50&skip=0
PUT /api/admin/users/{user_id}/block?reason=
PUT /api/admin/users/{user_id}/activate
```

### Vendors
```
GET /api/admin/vendors?status=pending&category_id=&limit=50
PUT /api/admin/vendors/{vendor_id}/approve
  ├── action: "approve" | "reject" | "suspend"
  └── reason: optional
PUT /api/admin/vendors/{vendor_id}/featured?featured=true
GET /api/admin/vendors/{vendor_id}/stats
```

### Bookings & Payments
```
GET /api/admin/bookings?status=confirmed&limit=50
GET /api/admin/payments?limit=50&skip=0
POST /api/admin/payments/{payment_id}/refund?reason=
```

### Audit Logs
```
GET /api/admin/audit-logs?admin_id=&action_type=&target_type=&limit=100
```

---

## 🛡️ Security Features

### Authentication & Authorization
- ✅ JWT-based authentication with role in token
- ✅ `admin_required` dependency on all admin routes
- ✅ Admin login with email + password validation
- ✅ Automatic redirect for non-admin users
- ✅ Session management with logout

### Audit Trail
- ✅ All admin actions logged with timestamp
- ✅ Admin ID and IP address recorded
- ✅ Action reason/comment tracked
- ✅ Success/failure status captured
- ✅ Comprehensive searchable audit logs

### Data Protection
- ✅ Pagination on sensitive data lists
- ✅ Password fields excluded from API responses
- ✅ Secure Razorpay integration
- ✅ Email notifications for critical actions
- ✅ Role-based filtering of visible data

---

## 🔧 Configuration

### Backend Environment Variables
```
JWT_SECRET_KEY=your_secret_key
MONGO_URL=mongodb://...
DB_NAME=shadiro
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_secret
RESEND_API_KEY=your_resend_key
```

### Frontend Environment Variables
```
REACT_APP_BACKEND_URL=http://localhost:8000
```

---

## 📊 Analytics & Reporting

The admin dashboard provides:
- **Real-time metrics** on platform health
- **Revenue tracking** with monthly breakdowns
- **Vendor performance** statistics
- **Category analysis** for demand insights
- **User growth** trends

---

## 🧪 Testing the Admin Module

### Prerequisites
1. An admin user account created
2. Sample vendors in different statuses
3. Sample orders and payments

### Test Scenarios

#### 1. Vendor Approval Flow
```
1. Navigate to /admin/vendors?status=pending
2. Click "Approve" on a pending vendor
3. Verify vendor status changes to "approved"
4. Verify email sent to vendor
5. Check audit log for the action
```

#### 2. User Moderation
```
1. Navigate to /admin/users
2. Search for a user
3. Click "Block" with a reason
4. Verify user marked as inactive
5. Use "Activate" button to reactivate
```

#### 3. Payment Refund
```
1. Navigate to /admin/payments
2. Find a completed payment
3. Click "Refund" and enter reason
4. Verify refund processed
5. Check payment status changed to "refunded"
```

#### 4. Audit Trail
```
1. Perform multiple admin actions
2. Navigate to /admin/audit-logs
3. Verify all actions appear with details
4. Filter by action_type or admin_id
5. Verify IP addresses and timestamps recorded
```

---

## 📱 Mobile Admin Support

While the current implementation is optimized for web/desktop, the API endpoints are RESTful and can be consumed by mobile apps:

```javascript
// Mobile implementation example
const adminApi = {
  getAnalytics: () => api.get('/admin/analytics'),
  approveVendor: (vendorId) => api.put(`/admin/vendors/${vendorId}/approve`),
  blockUser: (userId, reason) => api.put(`/admin/users/${userId}/block`, { reason }),
};
```

---

## 🚨 Common Issues & Solutions

### Issue: Admin can't login
**Solution:** Verify user role is set to "admin" in MongoDB
```javascript
db.users.findOne({email: "admin@example.com"})
```

### Issue: Audit logs not appearing
**Solution:** Ensure `admin_audit_logs` collection exists in MongoDB
```javascript
db.createCollection("admin_audit_logs")
```

### Issue: Vendor emails not sending
**Solution:** Verify RESEND_API_KEY is set and valid

### Issue: Refund fails
**Solution:** Ensure Razorpay credentials are correct and payment was previously successful

---

## 🔮 Future Enhancements

- ✅ Dispute resolution and manual override system
- ✅ Advanced analytics with exportable reports
- ✅ Vendor performance scoring
- ✅ Abuse reporting and review flagging
- ✅ Two-factor authentication for admins
- ✅ Role-based permissions (super-admin, moderator, etc.)
- ✅ Scheduled notifications and alerts
- ✅ Monthly revenue reports
- ✅ Admin activity dashboard with graphs

---

## 📞 Support

For questions or issues with the admin module:
1. Check the audit logs for detailed action history
2. Review error messages in browser console
3. Verify API credentials in environment variables
4. Check MongoDB connection status

---

**Last Updated:** February 2026  
**Version:** Phase 3  
**Status:** Production Ready ✅
