# Phase 3 Testing Guide

## 🧪 Test Execution Overview

This guide provides step-by-step instructions to test all Phase 3 features.

---

## 1️⃣ Setup & Prerequisites

### Install Dependencies (if not done)
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Start Services
```bash
# Terminal 1 - Backend
cd backend
python server.py
# Runs on http://localhost:8000

# Terminal 2 - Frontend  
cd frontend
npm start
# Runs on http://localhost:3000

# Terminal 3 - Database (if using Docker)
docker-compose up
```

### Create Test Data
```bash
# Run backend test setup
cd backend
python -c "
from init_db import initialize_database
import asyncio
asyncio.run(initialize_database())
"
```

---

## 2️⃣ Feature Testing Checklist

### Feature 1: Vendor Comparison (/compare)

**Test Case 1.1: Load Comparison Page**
- [ ] Navigate to `/compare`
- [ ] Page loads without errors
- [ ] Shows "No vendors selected" message

**Test Case 1.2: Add Vendors to Compare**
- [ ] Go to vendor listing
- [ ] Click any vendor detail
- [ ] Click "Add to Comparison" button
- [ ] Repeat for 2-3 vendors
- [ ] Button text changes to "Remove from Comparison"

**Test Case 1.3: View Comparison**
- [ ] Click "View Comparison" button
- [ ] Should navigate to `/compare?ids=id1,id2,id3`
- [ ] All selected vendors appear in table/cards
- [ ] Shows metrics: rating, reviews, price, experience, verification, featured

**Desktop Specific:**
- [ ] Table layout shows vendor names in columns
- [ ] Metrics are clearly visible and comparable
- [ ] All action buttons present

**Mobile Specific:**
- [ ] Cards stack vertically
- [ ] 1-2 vendors visible at once
- [ ] Can scroll horizontally to see more

**Test Case 1.4: Actions**
- [ ] Click "View Details" → navigates to vendor detail
- [ ] Click "Book Now" → navigates to booking flow
- [ ] Clear comparison → returns to listing

---

### Feature 2: Smart Planner Mode (/plan)

**Test Case 2.1: Step 1 - Event Details**
- [ ] Navigate to `/plan`
- [ ] Page displays event type selector
- [ ] 5 event types visible: Wedding, Corporate, Birthday, Engagement, Anniversary
- [ ] Can select event type (shows checkmark)
- [ ] Date picker appears and works
- [ ] Guest count input accepts numbers only
- [ ] Special requirements text area appears
- [ ] "Next Step" button enabled once required fields filled

**Test Case 2.2: Step 2 - Budget & Location**
- [ ] Click "Next Step"
- [ ] Step changes to "Budget & Location"
- [ ] City dropdown shows 8+ Indian cities
- [ ] Can select city (e.g., "Delhi", "Mumbai", "Bangalore")
- [ ] Budget input field accepts numeric values only
- [ ] Manual location text field appears
- [ ] Budget validation: rejects negative/zero values
- [ ] "View Bundles" button visible

**Test Case 2.3: Step 3 - Bundle Selection**
- [ ] Click "View Bundles"
- [ ] 3 bundles visible: Essential, Premium, Luxury
- [ ] Each bundle shows:
  - [ ] Bundle name and price
  - [ ] Number of vendors
  - [ ] Average rating
  - [ ] Category breakdown (Venue, Catering, etc.)
- [ ] Bundle prices follow formula: Essential=X, Premium=1.3X, Luxury=1.8X

**Test Case 2.4: Bundle Allocation Logic**
- [ ] Select budget: ₹5,00,000
- [ ] Essential bundle shows: ~₹5L total
- [ ] Premium shows: ~₹6.5L total  
- [ ] Luxury shows: ~₹9L total
- [ ] Venue: 30-35% of budget
- [ ] Catering: 25-30% of budget
- [ ] Decorators: 12-20% of budget

**Test Case 2.5: Selection & Continuation**
- [ ] Click on a bundle (e.g., Premium)
- [ ] Should navigate to vendor listing with filters applied
- [ ] Or display bundle confirmation with "Start Booking" button

---

### Feature 3: Event Timeline (Dashboard)

**Test Case 3.1: Timeline Display**
- [ ] Go to User Dashboard
- [ ] Scroll down or find "Event Timeline" section
- [ ] 5 phases visible:
  - [ ] Planning (Sparkles icon, purple)
  - [ ] Vendor Selection (Camera icon, blue)
  - [ ] Logistics (Utensils icon, orange)
  - [ ] Final Prep (Clock icon, amber)
  - [ ] Event Day (Zap icon, red)

**Test Case 3.2: Phase Detection (if event date is set)**
- [ ] Create/view an event with date 90 days away
- [ ] "Planning" phase should show as CURRENT (with badge)
- [ ] Other phases should show as UPCOMING
- [ ] If event is 7 days away, "Final Prep" should be CURRENT

**Test Case 3.3: Task Expansion**
- [ ] Click on any phase name or expand icon
- [ ] Phase expands to show task checklist (4 tasks per phase)
- [ ] Example tasks:
  - [ ] "Research & shortlist vendors"
  - [ ] "Get quotes from vendors"
  - [ ] "Compare options & negotiate"
  - [ ] "Book confirmed vendors"
- [ ] Can click checkbox to mark tasks complete

**Test Case 3.4: Progress Tracking**
- [ ] Check phase progress bar
- [ ] Bar fills proportionally as tasks are completed
- [ ] Shows percentage (0-100%)
- [ ] When all tasks done, shows "100%" and phase marked complete

**Test Case 3.5: Phase Completion**
- [ ] As event date approaches, phases automatically update status
- [ ] Past phases: COMPLETED (with checkmark)
- [ ] Current phase: CURRENT (with badge)
- [ ] Multiple check-ins at different event dates

---

### Feature 4: Vendor Availability Calendar

**Test Case 4.1: Access Calendar** (Two locations)
- [ ] Vendor Dashboard → "Manage Availability" section
- [ ] Vendor Detail Page → "Check Availability" section

**Test Case 4.2: Calendar Display**
- [ ] Calendar grid shows current month (7x7 grid)
- [ ] Days of week shown (Sun-Sat)
- [ ] Date numbers displayed
- [ ] Previous month's trailing dates grayed out
- [ ] Next month's leading dates grayed out

**Test Case 4.3: Past Dates Handling**
- [ ] All dates before today are grayed (50% opacity)
- [ ] Cannot click past dates
- [ ] Hover shows "Date not available" tooltip

**Test Case 4.4: Select Available Dates**
- [ ] For vendor mode: Click a future date
- [ ] Date highlights in green with checkmark
- [ ] Multiple dates selectable (clicking toggles)
- [ ] Selected dates show blue background + white text

**Test Case 4.5: Time Slot Selection**
- [ ] After selecting a date, time slots appear:
  - [ ] 09:00 - 12:00 (Morning)
  - [ ] 12:00 - 15:00 (Afternoon)
  - [ ] 15:00 - 18:00 (Late Afternoon)
  - [ ] 18:00 - 21:00 (Evening)
- [ ] Can select one or more time slots
- [ ] Selections are toggleable

**Test Case 4.6: Persistence**
- [ ] For vendors: Click "Save Availability"
- [ ] For users: Availability saves automatically
- [ ] On page refresh, selected dates still visible
- [ ] localStorage should contain availability data

**Test Case 4.7: Read-Only Mode**
- [ ] User viewing vendor detail sees read-only calendar
- [ ] Cannot click dates
- [ ] Shows only available dates in green
- [ ] Time slots shown but not selectable

---

### Feature 5: Emergency Cancellation

**Test Case 5.1: Trigger Emergency** (Vendor)
- [ ] Vendor Dashboard → Active Bookings
- [ ] Click "Emergency Cancel" on any booking
- [ ] Modal opens with:
  - [ ] Booking details (vendor, customer, date)
  - [ ] Reason field (required)
  - [ ] "Confirm Emergency Cancel" button
- [ ] Enter reason (e.g., "Staff illness")
- [ ] Click confirm

**Test Case 5.2: Immediate Response**
- [ ] Booking status changes to "CANCELLED_BY_VENDOR_EMERGENCY"
- [ ] Toast notification shows "Emergency cancelled"
- [ ] Vendor gets email confirmation
- [ ] Customer gets emergency notification with replacement options

**Test Case 5.3: Replacement Suggestions**
- [ ] System suggests replacement vendors:
  - [ ] Similar category
  - [ ] High rating (4.0+)
  - [ ] Available on event date
  - [ ] Budget compatible
- [ ] Show 3-5 suggestions to customer
- [ ] Customer can view each suggestion's profile

---

### Feature 6: Admin Emergency Dashboard (/admin/emergencies)

**Test Case 6.1: Access Dashboard**
- [ ] Login as admin
- [ ] Navigate to `/admin/emergencies`
- [ ] Dashboard loads without errors
- [ ] Admin has view permissions (non-admins get 403)

**Test Case 6.2: KPI Cards Display**
- [ ] Shows 5 metric cards:
  - [ ] "Total Emergencies": X (e.g., 15)
  - [ ] "Pending": X (e.g., 3)
  - [ ] "Resolved": X (e.g., 10)
  - [ ] "Avg Resolution Time": XX min
  - [ ] "Replacement Success Rate": XX%
- [ ] Cards have appropriate color coding
- [ ] Numbers update in real-time

**Test Case 6.3: Emergency List**
- [ ] Lists all emergencies as cards/rows
- [ ] Shows:
  - [ ] Status badge (color-coded)
  - [ ] Vendor name + rating
  - [ ] Customer name
  - [ ] Event date
  - [ ] Cancellation reason
  - [ ] Timestamp
- [ ] Can scroll through list

**Test Case 6.4: Filter & Sort** (if implemented)
- [ ] Filter by status: Pending, Resolved, Escalated
- [ ] Sort by date (newest/oldest)
- [ ] Search by vendor/customer name

**Test Case 6.5: Action Modal**
- [ ] Click on any emergency card
- [ ] Modal opens showing:
  - [ ] Full booking details
  - [ ] Cancellation reason
  - [ ] Customer info (name, email, phone)
  - [ ] Vendor info (name, alternate contact)
  - [ ] Replacement suggestions (if any)
- [ ] Has action form with:
  - [ ] Status: Shows current status
  - [ ] Notes field (required for actions)
  - [ ] Three action buttons

**Test Case 6.6: Action 1 - Approve Replacement**
- [ ] Click "Approve Replacement" button
- [ ] Success message: "Emergency resolved"
- [ ] Booking status: → RESOLVED
- [ ] New booking created with replacement vendor
- [ ] Original booking linked via `is_replacement_for`
- [ ] New booking inherits: date, guests, budget, services

**Test Case 6.7: Action 2 - Initiate Refund**
- [ ] Previous status shows one emergency resolved
- [ ] Click another emergency → "Initiate Refund" button
- [ ] Booking status: → REFUNDED
- [ ] Customer receives email: "Refund initiated for booking"
- [ ] Notification shows refund amount
- [ ] KPI "Resolved" count increases

**Test Case 6.8: Action 3 - Escalate**
- [ ] Click another emergency → "Escalate" button
- [ ] Notes become required
- [ ] Enter note: "Customer unsatisfied with replacements"
- [ ] Click escalate
- [ ] Booking status: → ESCALATED
- [ ] Admin team receives email with escalation reason
- [ ] Card shows "ESCALATED" status

**Test Case 6.9: Emergency Status Flow**
- [ ] New emergency starts as PENDING
- [ ] After any admin action: RESOLVED, REFUNDED, or ESCALATED
- [ ] Cannot change status after resolution (disabled buttons)
- [ ] Non-pending emergencies show: "Emergency resolved - [Action taken]"

---

## 3️⃣ Backend Integration Tests

### Test Emergency Endpoints

**Setup:**
```bash
# Get auth token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"pass123"}'

# Save the token
TOKEN="eyJ0eXAi..."
```

**Test 1: Get Emergency Bookings** ✅
```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/bookings/emergencies/list?skip=0&limit=10"

# Expected: 200 OK with array of emergency bookings enriched with vendor/user names
```

**Test 2: Approve Replacement** ✅
```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "replacement_vendor_id":"vendor123",
    "notes":"Approved replacement with high-rated vendor"
  }' \
  "http://localhost:8000/api/bookings/booking123/approve-replacement"

# Expected: 200 OK, booking status → "resolved"
```

**Test 3: Initiate Refund** ✅
```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes":"Refund approved due to vendor unavailability"}' \
  "http://localhost:8000/api/bookings/booking123/initiate-refund"

# Expected: 200 OK, booking status → "refunded"
```

**Test 4: Escalate Emergency** ✅
```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Customer requesting specific vendor not in suggestions"}' \
  "http://localhost:8000/api/bookings/booking123/escalate"

# Expected: 200 OK, booking status → "escalated"
```

---

## 4️⃣ Data Validation Tests

### Test Input Validation

**Vendor Comparison:**
- [ ] Valid vendor IDs format
- [ ] Invalid IDs return 404
- [ ] Too many vendors (>5) handled gracefully
- [ ] Duplicate IDs ignored

**Planner Mode:**
- [ ] Event type is required
- [ ] Date must be future date
- [ ] Guest count: 1-10000 range
- [ ] Budget: ₹50k - ₹100L range
- [ ] City must be from predefined list
- [ ] Special requirements: optional

**Calendar:**
- [ ] Cannot select past dates
- [ ] Can select future dates
- [ ] Time slots are valid (within business hours)
- [ ] Duplicate selections disabled

**Emergency:**
- [ ] Reason required (min 10 chars)
- [ ] Cannot cancel non-active bookings
- [ ] Vendor must own the booking
- [ ] Admin reason required (min 5 chars)

---

## 5️⃣ UI/UX Tests

### Responsiveness
- [ ] Visit each page on: iPhone (375px), iPad (768px), Desktop (1440px)
- [ ] No horizontal scroll on mobile
- [ ] Text readable on all sizes
- [ ] Buttons clickable (touch-friendly > 44px)
- [ ] Images scale appropriately

### Accessibility
- [ ] Can tab through all interactive elements
- [ ] Colors have sufficient contrast (WCAG AA)
- [ ] Form labels associated with inputs
- [ ] Error messages clear and visible
- [ ] Modals have close buttons

### Loading States
- [ ] Loading spinners appear while fetching
- [ ] Forms disable on submission
- [ ] Buttons show loading text
- [ ] Images show skeleton loading
- [ ] Timeout handling (> 5s shows error)

### Error Handling
- [ ] Network errors show toast notification
- [ ] Form validation shows field errors
- [ ] Invalid token shows 401 error
- [ ] Delete operations show confirmation
- [ ] Undo option available (where applicable)

---

## 6️⃣ Performance Tests

### Metrics to Check
- [ ] Initial page load: < 3s
- [ ] Component render: < 100ms
- [ ] API response: < 500ms
- [ ] Bundle size: < 500KB (gzip)

### Browser DevTools (F12)
1. **Network Tab:**
   - Requests < 100ms? ✅
   - Waterfall loading optimal? ✅
   - No 404 errors? ✅

2. **Performance Tab:**
   - Record: Navigate → Planner Mode
   - FCP < 2s? ✅
   - LCP < 3s? ✅
   - CLS < 0.1? ✅

3. **Memory Tab:**
   - No memory leaks on route change
   - Heap size stable
   - No unused variables

---

## 7️⃣ End-to-End Workflow Tests

### Workflow 1: Emergency Resolution (Full Flow)
```
1. Vendor: Books confirmed at 2:30 PM
2. Vendor: At 2:15 PM triggers emergency (staff illness)
3. System: Marks booking CANCELLED_BY_VENDOR_EMERGENCY
4. System: Finds 3 replacements
5. Customer: Receives notification + suggestions
6. Customer: Views replacement vendor profiles
7. Customer: Selects "Premium Caterer" as replacement (or chooses refund)
8. Admin: Views emergency in dashboard
9. Admin: Approves selected replacement
10. System: Creates new booking with replacement vendor
11. System: Updates original booking (RESOLVED)
12. Customer: Receives confirmation of replacement
13. Vendor: Receives new booking notification
Result: ✅ Event is still happening with different vendor
```

### Workflow 2: Smart Event Planning
```
1. User: Clicks "Plan My Event"
2. User: Selects Wedding, March 30, 150 guests, budget ₹10L
3. User: Selects Mumbai, exact location
4. System: Shows 3 bundles:
   - Essential: ₹10L
   - Premium: ₹13L
   - Luxury: ₹18L
5. User: Clicks Premium bundle
6. System: Pre-fills budget allocation:
   - Venue: ₹3.5L
   - Catering: ₹3L
   - Decorators: ₹1.5L
   - DJ/Entertainment: ₹1.5L
   - Photography: ₹1.5L
7. User: Sees recommended vendors matching budget
8. User: Compares 2-3 venues side-by-side
9. User: Books venue + catering + photographer
10. System: Shows event timeline
Result: ✅ Event fully planned within 10 min
```

### Workflow 3: Vendor Comparison
```
1. User: Browsing vendor listings
2. User: Sees "Compare" button on 3 venue vendors
3. User: Clicks "Add to Compare" on vendor A, B, C
4. User: User Sees "View Comparison" button
5. User: Clicks comparison link
6. System: Shows side-by-side table:
   Metrics:     | Vendor A | Vendor B | Vendor C
   Rating:      |   4.8    |   4.5    |   4.9
   Reviews:     |   128    |    95    |   156
   Price/Head:  |   4500   |   4000   |   5500
   Experience:  |   8 yrs  |   5 yrs  |   10 yrs
   Verification: ✓       |   ✓      |   ✓
   Featured:    |   ✓      |    -     |   ✓
7. User: Clicks "Book Now" on Vendor C (highest rating)
8. User: Proceeds to booking flow
Result: ✅ Cost/quality decision made in 2 min
```

---

## 8️⃣ Debug Commands

### Frontend Debugging
```javascript
// In browser console:

// Check current routes
console.log(window.location.pathname)

// Check component props
console.log(props)

// Monitor API calls
fetch('http://localhost:8000/api/...').then(r => r.json()).then(console.log)

// Check localStorage
console.log(localStorage.getItem('eventTimeline'))
console.log(localStorage.getItem('vendorComparison'))
```

### Backend Debugging
```python
# In Python terminal:
import requests
import json

# Test endpoint
resp = requests.get(
    'http://localhost:8000/api/bookings/emergencies/list',
    headers={'Authorization': f'Bearer {token}'}
)
print(json.dumps(resp.json(), indent=2))

# Check for errors
print(resp.status_code)
print(resp.text)
```

---

## Summary Checklist

**Before Launch:**
- [ ] All 8 features working
- [ ] Mobile responsive verified
- [ ] Error handling tested
- [ ] 25+ test cases passed
- [ ] Performance acceptable
- [ ] Accessibility verified
- [ ] Documentation complete

**Total Test Coverage:**
- ✅ 6 Features
- ✅ 40+ Test Cases  
- ✅ 5 Workflows
- ✅ API Integration
- ✅ Data Validation
