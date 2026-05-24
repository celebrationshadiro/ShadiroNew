# 🎯 Admin Module - Quick Reference & Examples

## Access the Admin Panel

### 1. Login to Admin Panel
```
URL: http://localhost:3000/admin/login
Email: your_admin_email@example.com
Password: your_admin_password
```

### 2. Verify Role in Database
```javascript
// MongoDB - Check if user is admin
db.users.findOne({email: "admin@example.com"})
// Output should include: role: "admin"

// If not admin, update:
db.users.updateOne(
  {email: "admin@example.com"},
  {$set: {role: "admin"}}
)
```

---

## 📊 Dashboard Navigation

### Main Menu Items
1. **Dashboard** - Analytics & KPIs
2. **Vendors** - Approval & management
3. **Users** - Account management
4. **Bookings** - Order management
5. **Payments** - Refunds & history
6. **Audit Logs** - Action history
7. **Logout** - Exit admin panel

---

## 🔍 Common Admin Tasks

### Task 1: Approve a Pending Vendor

**Step-by-step:**
```
1. Click "Vendors" in sidebar
2. Filter by "pending"
3. Click "Approve" button on vendor
4. Vendor marked as "approved"
5. Email sent to vendor automatically
6. Action logged in audit trail
```

**HTTP Response:**
```json
{
  "message": "Vendor approved",
  "status": "approved"
}
```

**Audit Log Entry:**
```json
{
  "action_type": "vendor_approve",
  "admin_id": "admin_user_id",
  "target_id": "vendor_id",
  "details": {"vendor_name": "Wedding Services Co"},
  "success": true
}
```

---

### Task 2: Reject a Vendor with Reason

**Step-by-step:**
```
1. Click "Vendors" in sidebar
2. Filter by "pending"
3. Click "X" (reject) button
4. Modal appears asking for reason
5. Enter reason: "Incomplete documentation"
6. Click "Reject"
7. Vendor marked as "rejected"
8. Rejection email sent with reason
9. Action logged with reason
```

**Rejection Email Includes:**
- Rejection notice
- Specific reason provided
- Support contact information

---

### Task 3: Block a Problematic User

**Step-by-step:**
```
1. Click "Users" in sidebar
2. Search for user by name or email
3. Click "Block" button
4. Modal asks for block reason
5. Enter: "Abusive behavior in messages"
6. Click "Block"
7. User marked as "Blocked"
8. User cannot login anymore
9. Admin recorded in audit
```

**Result:**
- User is_active = false
- Login attempts rejected
- Account can be reactivated later

---

### Task 4: Process Payment Refund

**Step-by-step:**
```
1. Click "Payments" in sidebar
2. Find successful payment (green status)
3. Click "Refund" button
4. Prompt asks for refund reason
5. Enter: "Customer requested duplicate charge reversal"
6. System processes refund via Razorpay
7. Payment status changes to "refunded"
8. Refund ID recorded
9. Action logged with reason
```

**Statistics Updated:**
- "Refunded Amount" increases
- "Successful Payments" count may adjust
- Revenue recalculated

---

### Task 5: View Vendor Performance Stats

**Step-by-step:**
```
1. Click "Vendors" in sidebar
2. Click "Stats" button on any vendor
3. See popup with:
   - Total Bookings: 15
   - Confirmed Bookings: 12
   - Total Revenue: ₹150,000
   - Average Rating: 4.5 ⭐
   - Number of Reviews: 8
4. Close popup and continue browsing
```

**Available Metrics:**
```json
{
  "total_bookings": 15,
  "confirmed_bookings": 12,
  "total_revenue": 150000,
  "average_rating": 4.5,
  "total_reviews": 8,
  "status": "approved",
  "is_featured": false
}
```

---

### Task 6: View Complete Audit Trail

**Step-by-step:**
```
1. Click "Audit Logs" in sidebar
2. See complete action history with:
   - Admin who did action
   - What action (color coded)
   - Target entity and ID
   - Reason/comment
   - Timestamp
   - IP address
3. Filter by admin_id or action_type
4. Use pagination to browse
```

**Example Audit Log Entry:**
```json
{
  "id": "log_abc123",
  "admin_id": "admin_001",
  "action_type": "vendor_suspend",
  "target_type": "vendor",
  "target_id": "vendor_123",
  "reason": "Breach of service agreement",
  "details": {"vendor_name": "Event Pro Services"},
  "created_at": "2026-02-10T14:30:00Z",
  "ip_address": "192.168.1.100",
  "success": true
}
```

---

## 🔍 Searching & Filtering

### Users Page
```
Search Box: Type name or email
├── "John" → finds all Johns
├── "john@example.com" → exact match
└── "smith" → finds Smiths

Role Filter Dropdown:
├── All Roles
├── Admin
├── Vendor
└── User

Status Filter Dropdown:
├── All Status
├── Active
└── Blocked
```

### Vendors Page
```
Status Filter Buttons:
├── All (shows all vendors)
├── Pending (approval in progress)
├── Approved (live on platform)
├── Rejected (application denied)
└── Suspended (account frozen)
```

### Payments Page
```
Automatic Sorting: Most recent first

Status Badges:
├── Success (green) - Completed successfully
├── Pending (amber) - Still processing
├── Failed (red) - Transaction failed
└── Refunded (blue) - Money returned to customer
```

---

## 📈 Understanding Analytics Dashboard

### Key Metrics Explained

**Total Users**
- Count of all registered users
- Includes: Users + Vendors + Admins

**Total Vendors**
- Count of all vendor accounts
- Includes: Pending, Approved, Suspended, Rejected

**Pending Approvals**
- Vendors awaiting admin review
- Action needed from admin

**Total Revenue**
- Sum of all confirmed order totals
- From completed transactions only

**Monthly Bookings Chart**
- Last 6 months of confirmed orders
- Shows platform growth trend
- Y-axis: Number of bookings
- X-axis: Month (YYYY-MM format)

**Category Demand Chart**
- Number of vendors per category
- Shows market concentration
- Helps identify growth opportunities

---

## 🛠️ API Examples for Developers

### Using Admin API in Code

```javascript
// Get dashboard analytics
const analytics = await admin.getAnalytics();
console.log(analytics.total_users); // 250
console.log(analytics.total_revenue); // 50000

// Get all users
const users = await admin.getUsers({
  search: "john",
  role: "vendor",
  limit: 50,
  skip: 0
});

// Block a user
const result = await admin.blockUser(userId, "Abusive behavior");

// Get vendor stats
const stats = await admin.getVendorStats(vendorId);
console.log(stats.total_revenue); // ₹150,000

// Process refund
const refund = await admin.refundPayment(paymentId, "Duplicate charge");

// Get audit logs
const logs = await admin.getAuditLogs({
  admin_id: "admin_001",
  action_type: "vendor_approve",
  limit: 100
});
```

---

## 🔐 Security Tips for Admins

1. **Strong Passwords**
   - Use 12+ character passwords
   - Include: uppercase, lowercase, numbers, symbols

2. **Don't Share Credentials**
   - Each admin should have own account
   - Actions are tracked to admin ID

3. **Logout After Sessions**
   - Click "Logout" when done
   - Session expires after inactivity

4. **Verify Actions**
   - Check audit logs to verify your actions
   - Watch for suspicious activity

5. **Report Issues**
   - Contact support for:
     - Failed refunds
     - Email delivery issues
     - Database errors

---

## 🐛 Troubleshooting

### Problem: Can't login to admin panel
```
✓ Verify user role is "admin"
  db.users.findOne({email: "admin@example.com"})
✓ Check password is correct
✓ Clear browser cache and retry
✓ Verify JWT_SECRET_KEY in .env
```

### Problem: Vendor approval email not sending
```
✓ Verify RESEND_API_KEY is set
✓ Check vendor email is valid
✓ View backend logs for errors:
  tail -f /logs/backend.log
✓ Test email service:
  POST /api/test/send-email
```

### Problem: Refund processed but status didn't change
```
✓ Refresh page (F5)
✓ Check Razorpay dashboard for refund status
✓ Verify payment ID is correct
✓ Check MongoDB for payment record update
```

### Problem: Audit logs not appearing
```
✓ Verify admin_audit_logs collection exists
  db.getCollectionNames()
✓ Check if actions were actually performed
✓ Wait a moment for async logging to complete
✓ Refresh page to see latest
```

---

## 📞 Emergency Contacts

For critical issues:

**Email:** admin-support@shadiro.com
**Phone:** +1-XXX-XXX-XXXX
**Slack:** #admin-support

---

## 📋 Admin Responsibilities Checklist

- [ ] Review pending vendor applications daily
- [ ] Monitor user complaints and reports
- [ ] Process refunds within 24 hours
- [ ] Check audit logs weekly
- [ ] Block abusive users promptly
- [ ] Feature high-quality vendors
- [ ] Monitor platform revenue
- [ ] Backup admin_audit_logs collection monthly

---

## 🎓 Examples & Scenarios

### Scenario 1: Wedding Vendor Onboarding
```
Day 1: Vendor submits application
- Status: pending
- Admin notified

Day 2: Admin reviews
- Verifies business documents
- Checks reviews if transferring

Day 3: Admin approves
- Status: approved
- Vendor receives email
- Can accept bookings

Day 7: Admin features vendor
- Marked as featured
- Appears in featured section
```

### Scenario 2: Handling Complaint
```
Day 1: Customer files complaint
- Reports vendor for unprofessional behavior

Day 2: Admin investigates
- Views chats/messages
- Checks vendor history

Day 3: Admin suspends vendor
- Vendor can't receive new bookings
- Existing bookings unaffected

Day 4: Admin and vendor discuss
- Vendor submits response

Day 5: Admin decides
- Reactivate (if satisfactory)
- Permanent rejection (if serious)
```

---

## 🎨 UI Component Reference

### Common Buttons
```
Primary (Blue): Main actions
├── Approve ✓
├── Block
└── Activate

Danger (Red): Destructive actions
├── Reject X
├── Suspend
└── Refund

Secondary (Gray): Optional actions
├── View
├── Cancel
└── More Options
```

### Status Badges
```
Green: Approved, Active, Success
Amber: Pending, Processing
Red: Rejected, Failed, Blocked, Suspended
Blue: Refunded
Gray: Inactive
```

---

## 📱 Mobile Admin Access

While the UI is optimized for desktop, you can:
- Access on mobile browser
- Full functionality available
- Responsive layout adapts
- Recommended: Use landscape mode for better view

---

## 📚 Related Documentation

- See: [ADMIN_MODULE_GUIDE.md](./ADMIN_MODULE_GUIDE.md) - Full implementation guide
- See: [PHASE3_ADMIN_IMPLEMENTATION.md](./PHASE3_ADMIN_IMPLEMENTATION.md) - Technical summary
- See: Backend code comments for API details

---

**Last Updated:** February 2026  
**Maintained By:** Admin Team  
**Support:** admin-support@shadiro.com  

✅ **All Features Working**
✅ **Tested & Verified**
✅ **Production Ready**
