# Shadiro Platform - UI/UX Design Specifications

## Version 1.0 | February 9, 2026

---

## 📋 Table of Contents
1. [Design Principles](#design-principles)
2. [Home Screen](#home-screen)
3. [Vendor Listing Page](#vendor-listing-page)
4. [Vendor Detail Page](#vendor-detail-page)
5. [Dynamic Services UI by Vendor Type](#dynamic-services-ui)
6. [Booking Flow & Summary](#booking-flow)
7. [Premium Chat UI](#chat-ui)
8. [Notifications & Alerts](#notifications)
9. [Vendor Dashboard](#vendor-dashboard)
10. [Admin Panel](#admin-panel)
11. [Emergency Cancellation Flows](#emergency-flows)
12. [Micro-Interactions](#micro-interactions)
13. [Responsive Design](#responsive-design)

---

## Design Principles

### Core Pillars
- **Premium**: Luxurious spacing, refined typography, quality imagery
- **Trustworthy**: Clear information architecture, transparent pricing, verified badges
- **Smooth**: Micro-animations, seamless transitions, loading states
- **Simple**: Minimal UI, clear CTAs, non-technical language
- **Scalable**: Component-based, vendor-type adaptable, multi-platform

### Visual Hierarchy
```
Primary Action (CTA) → Deep Rose (#BE185D)
Secondary Action → Charcoal (#1F2937) 
Accent Elements → Gold (#F59E0B)
Background & Surfaces → Soft White (#FAFAFA)
Text → Charcoal (#1F2937)
Supporting Text → Gray (#6B7280)
```

---

## Home Screen

### Mobile Version
```
┌─────────────────────────────┐
│  ← Shadiro        Menu  ☐   │  [Header: Minimal, app name + hamburger]
├─────────────────────────────┤
│                             │
│  Plan your perfect event,   │  [Hero Banner: 200px height]
│     effortlessly            │  Gradient: #BE185D → #9D174D
│                             │  CTA: "Explore Vendors"
├─────────────────────────────┤
│ Quick Event Actions:        │  [4-column grid]
│ ┌─────┐ ┌─────┐ ┌─────┐   │
│ │💍   │ │🎂   │ │🎉   │    │
│ │Wed  │ │Birth│ │Corp │    │
│ └─────┘ └─────┘ └─────┘    │
│        ┌─────┐               │
│        │⚙️ Custom            │
│        │Event                │
│        └─────┘               │
├─────────────────────────────┤
│ 🔥 Trending Near You:       │  [Horizontal Scroll]
│ ┌──────────────┐            │
│ │ [Image]      │ Caterer   │
│ │ ⭐4.8 (234)  │ 3km away  │
│ │ Est. ₹2000   │           │
│ │ Book Now →   │           │
│ └──────────────┘            │
│                             │
│ ┌──────────────┐            │
│ │ [Image]      │ DJ         │
│ │ ⭐4.9 (412)  │ 2km away  │
│ │ Est. ₹5000   │           │
│ │ Book Now →   │           │
│ └──────────────┘            │
├─────────────────────────────┤
│ ✅ Trusted Vendors:         │  [With verified checkmark]
│ [Cards with verified badges]│
├─────────────────────────────┤
│ Home │Search │Book │Chat │👤│ [Bottom Navigation]
└─────────────────────────────┘
```

### Desktop Version
- **Left Sidebar**: Navigation
- **Hero Section**: Full-width background image + overlay text + CTA button
- **Quick Actions**: 4-column grid (Wedding, Birthday, Corporate, Custom)
- **Recommended Vendors**: 3-column grid with carousel
- **Popular Near You**: Horizontal scroll or 3-column grid
- **Trusted Vendors**: 3-column grid with verified badges

### Components
- **Hero Banner**
  - Height: 300px (desktop), 200px (mobile)
  - Background: Gradient + semi-transparent overlay
  - Text: White, centered, h1 + lead text
  - CTA Button: Primary style, prominent
  - Image Overlay: 60% dark gradient

- **Quick Action Cards**
  - Size: 100x100px (mobile), 140x140px (desktop)
  - Background: Light gradient (custom per type)
  - Icon: 48px, centered
  - Label: Caption size, centered
  - On Tap: Navigate to filtered vendor list

- **Vendor Preview Card** (Trending/Popular/Trusted)
  - **Image**: Aspect ratio 16:9, rounded top
  - **Info Section**: 
    ```
    Vendor Name (h4)
    ⭐ 4.8 (234 reviews) | Distance: 3km
    Est. Price Range: ₹2000 - ₹5000
    Category Chips: [Catering] [Vegetarian] [Delivery]
    CTA: "Book Now" (Primary) | "Request Quote" (Secondary)
    ```
  - **Spacing**: 16px padding
  - **Shadow**: Medium on hover, premium shadow on interact
  - **Verified Badge**: Gold checkmark (top-right corner)

---

## Vendor Listing Page

### Layout Structure

```
┌─────────────────────────────────────────────┐
│ ← Vendors       [🔍 Search] [⚙️ Filter]     │  [Header with search + filter]
├─────────────────────────────────────────────┤
│ Showing 24 vendors matching your search     │
├─────────────────────────────────────────────┤
│                                             │
│ ┌────────────────┐ ┌────────────────┐     │  [2-column on mobile, 3 on tablet, 4 on desktop]
│ │ [Image 16:9]   │ │ [Image 16:9]   │     │
│ │ Vendor Name    │ │ Vendor Name    │     │
│ │ ⭐ 4.8 (234)   │ │ ⭐ 4.7 (189)   │     │
│ │ Est. ₹2000-3000│ │ Est. ₹3000-4000│     │
│ │ 3km | ✅ Avail │ │ 2km | ✅ Avail │     │
│ │ [Book] [Quote] │ │ [Book] [Quote] │     │
│ └────────────────┘ └────────────────┘     │
│                                             │
│ ┌────────────────┐ ┌────────────────┐     │
│ │ [Image 16:9]   │ │ [Image 16:9]   │     │
│ │ ...            │ │ ...            │     │
│ └────────────────┘ └────────────────┘     │
│                                             │
│ [Load More] or [Infinite Scroll]           │
└─────────────────────────────────────────────┘
```

### Filter Panel

**Mobile**: Bottom sheet or collapse/expand (below vendor type chip buttons)

**Desktop**: Sticky left sidebar or collapsible panel

```
Filters (× Clear All)

📍 Location
  [Map View] [Radius: 5km ▼]

💰 Price Range
  ₹0 ———————●——— ₹50,000
  From: [₹0]     To: [₹50,000]

⭐ Rating
  ☐ 4.0+ up
  ☐ 3.5+
  ☐ 3.0+
  ☐ All

📅 Availability
  Date: [Feb 15, 2026 ▼]

🏷️ Vendor Type
  ☐ Catering (12)
  ☐ DJ (8)
  ☐ Decor (15)
  ☐ Grocery (20)
  ☐ Planner (5)

[Apply Filters] [Reset]
```

### Vendor Card Details

**Card Structure** (16px border radius, 1px border #F3F4F6, md shadow):
```
┌─────────────────────────┐
│                         │
│   [Image: 16:9 ratio]   │  ← Rounded top, overflow hidden
│                         │
├─────────────────────────┤
│ Vendor Name (h4)        │
│ ⭐ 4.8 (234 reviews)    │  ← Smaller text
│ Category: [DJ] [Sound]  │
│ Est. ₹2000 - ₹5000      │
│ 3km away • ✅ Available │
│ [Book Now] [Request]    │  ← Two buttons, full width
└─────────────────────────┘
```

### Search Experience
- **Search Bar**: Sticky at top, full width, with clear (×) button
- **Search Suggestions**: Dropdown showing recent searches + categories
- **No Results**: Show filtered categories + "Try adjusting filters" CTA
- **Loading**: Skeleton cards while fetching

---

## Vendor Detail Page

### Header Section

```
┌─────────────────────────────────────────────┐
│                                             │
│  [Image Carousel: Full width, 300px height]│
│  ◄ [Indicators] ►                          │  ← Image dots + arrows
│  ❤️ (top-right)                            │  ← Wishlist button
│                                             │
├─────────────────────────────────────────────┤
│ Vendor Name                          ✅     │  ← Verified checkmark on right
│ ⭐ 4.8/5 (234 reviews)              📍 3km │
│ Category: [Catering] [North Indian] [Veg]  │
│ Price Range: ₹2000 - ₹50,000               │
│                                             │
│ [Request Quote] [Book Now] (primary, full) │
├─────────────────────────────────────────────┤
│ Tab Navigation:                             │  ← Sticky on scroll
│ Overview │ Services │ Packages │ Reviews    │
│          │         │          │            │
```

### Tab 1: Overview

```
About the Vendor
─────────────────
"We provide premium catering services for weddings,
corporate events, and celebrations. 10+ years of experience..."

📊 Stats
- 450+ Events Delivered
- 98% Client Satisfaction
- Avg. Rating: 4.8/5
- Response Time: < 2 hours

🏆 Highlights
✓ Serves 100-5000 guests
✓ Customizable menus
✓ Professional staff
✓ Eco-friendly packaging

📸 Gallery
[Image 1] [Image 2] [Image 3] [Image 4]

🎖️ Certifications
✓ Food Safety Certified
✓ ISO 9001:2015
```

### Tab 2: Services / Items

**Dynamic UI based on vendor type** (See detailed section below)

### Tab 3: Packages

```
Choose a Package:

📦 Basic Package (Popular)
├ 2-course meal
├ 20 guests minimum
├ Disposable service ware
└ ₹1500/guest → [View Details]

📦 Premium Package (Best Value)
├ 3-course meal
├ 50 guests minimum
├ Ceramic service ware
├ Live counter
└ ₹2500/guest → [View Details]

📦 Luxury Package (Exclusive)
├ 5-course meal
├ 100+ guests
├ Premium décor
├ Chef + Assistant
└ ₹5000/guest → [View Details]
```

### Tab 4: Reviews

```
⭐ 4.8/5 based on 234 reviews

Filter: [All] [⭐⭐⭐⭐⭐] [⭐⭐⭐⭐] [Recent]

User Avatar  Priya Singh    ⭐⭐⭐⭐⭐
Feb 2, 2026
"Amazing catering! Food was delicious and service
was impeccable. Highly recommended!"
❤️ Helpful (23)

User Avatar  Rahul Verma    ⭐⭐⭐⭐
Jan 28, 2026
"Good food and service. A bit pricey but worth it."
❤️ Helpful (8)
```

### Tab 5: About Vendor

```
Business Details
─────────────────
Owner: Ramesh Kumar
Years in Business: 12
Service Area: 2-10km radius
Languages Spoken: English, Hindi, Marathi

Reviews & Credentials
─────────────────────
✅ Email Verified
✅ Phone Verified
✅ License Verified (Food FSSAI)

Response Time
─────────────
Average: < 2 hours
Response Rate: 98%
```

---

## Dynamic Services UI by Vendor Type

### 1. Grocery Vendor UI

```
┌─────────────────────────────────────────────┐
│ Category Filter Chips:                      │
│ [Rice] [Dal] [Oil] [Spices] [Vegetables]   │
├─────────────────────────────────────────────┤
│                                             │
│ RICE                                    ˅   │ ← Accordion expand/collapse
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ Basmati Rice (Premium) - ₹120/kg     │   │
│ │ ⭐4.9 | 450 purchases                │   │
│ │ Qty: [-] 0 kg [+]                    │   │  ← Quantity selector
│ │ Subtotal: ₹0                         │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ Jasmine Rice - ₹90/kg                │   │
│ │ ⭐4.7 | 320 purchases                │   │
│ │ Qty: [-] 0 kg [+]                    │   │
│ │ Subtotal: ₹0                         │   │
│ └──────────────────────────────────────┘   │
│                                             │
│ DAL                                     ˅   │ ← Collapsed section
│                                             │
├─────────────────────────────────────────────┤
│ 📌 STICKY BOTTOM BAR                        │
│ Total: ₹2,840                              │
│ Items: 8                                    │
│   [Continue Shopping] [Add to Booking]     │ ← Primary CTA
└─────────────────────────────────────────────┘
```

**Item Card Design (Per Product)**
- **Layout**: Horizontal card, left image (80x80px), right info
- **Title**: Item name in h4, slightly bold
- **Rating**: Star + count
- **Price**: Large, bold, primary color
- **Quantity Selector**: [-] Counter [+] (with increment/decrement buttons)
- **Real-time Subtotal**: Updates on quantity change
- **Add-ons checkbox**: "Gift wrap?" "$10"

### 2. DJ Vendor UI

```
┌─────────────────────────────────────────────┐
│ Duration Selector:                          │
│ ○ 2 Hours  ○ 4 Hours  ○ 6 Hours ○ Full Day│
│ (Updates pricing in real-time)              │
├─────────────────────────────────────────────┤
│                                             │
│ Core Services:                              │
│                                             │
│ ☑ DJ + Sound System (Included)             │  ← Checkbox toggle
│   ₹3,000/hour                              │
│                                             │
│ ☐ LED Lighting Package                     │
│   + ₹1,500/hour                            │
│                                             │
│ ☐ DJ Trolley with Smoke                    │
│   + ₹800/hour                              │
│                                             │
│ ☐ Backup DJ (Recommended)                  │
│   + ₹2,000/hour                            │
│                                             │
├─────────────────────────────────────────────┤
│ Add-ons:                                    │
│                                             │
│ 🎤 ☐ Wireless Microphone (x2)              │
│      + ₹500                                 │
│                                             │
│ 🎸 ☐ Live Band Integration                 │
│      + ₹5,000                              │
│                                             │
├─────────────────────────────────────────────┤
│ 📌 STICKY BOTTOM BAR                        │
│ Total: ₹12,000 (4 hours)                   │
│   [Edit Duration] [Add to Booking]         │
└─────────────────────────────────────────────┘
```

**Key Features**
- **Duration Toggle**: Changes all pricing instantly
- **Service Cards**: Checkbox + label + price delta
- **Visual Hierarchy**: Core service highlighted, add-ons secondary
- **Real-time Calculation**: Total updates as selections change

### 3. Wedding Planner / Decor Vendor UI

```
┌─────────────────────────────────────────────┐
│ Wedding Theme Selection:                    │
│                                             │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ │ Traditional│ │ Modern  │ │ Beach   │    │
│ │ Theme      │ │ Minimal │ │ Tropical│    │
│ │ ₹25,000    │ │ ₹18,000 │ │ ₹22,000 │    │
│ │ Selected:✓ │ │         │ │         │    │
│ └──────────┘ └──────────┘ └──────────┘    │
│                                             │
├─────────────────────────────────────────────┤
│ Venue Setup:                                │
│                                             │
│ ☑ Full Venue Setup (Inside & Outside)      │
│   Includes: Décor, Seating, Lighting       │
│   ₹15,000 (Included in theme)              │
│                                             │
│ ☐ Partial Setup (Decoration Only)          │
│   - ₹8,000                                 │
│                                             │
│ ☐ I have my own venue                      │
│   [Show venue-specific addons]             │
│                                             │
├─────────────────────────────────────────────┤
│ Additional Services:                        │
│                                             │
│ ☐ Pre-wedding Photoshoot Setup             │
│   + ₹3,000                                 │
│                                             │
│ ☐ Mehendi Function Décor                   │
│   + ₹8,000                                 │
│                                             │
│ ☐ Baraat Entrance Setup                    │
│   + ₹5,000                                 │
│                                             │
├─────────────────────────────────────────────┤
│ 📌 STICKY BOTTOM BAR                        │
│ Total: ₹33,000                             │
│ Theme: Traditional                         │
│ Venue: Full Setup                          │
│   [Customize] [Add to Booking]             │
└─────────────────────────────────────────────┘
```

**Key Features**
- **Theme Cards**: Image + name + price + selection radio
- **Venue Options**: Conditional UI (if custom venue selected, show different addons)
- **Visual Grouping**: Services grouped logically
- **Price Transparency**: All prices clearly shown, total updates realistically

---

## Booking Flow

### Step 1: Service Confirmation

```
Review Your Selection
─────────────────────
Service: DJ + Sound System (Catering)
Duration: 4 Hours

Items Selected:
  • Basmati Rice (1kg) - ₹120
  • Jasmine Rice (2kg) - ₹180
  • Total: 5 items

Date: Feb 15, 2026
Time: 6:00 PM - 10:00 PM

[Edit Selection] [Proceed] (Primary button, full width)
```

### Step 2: Booking Details

```
Booking Address & Details
────────────────────────────
Delivery Address:
Block A, Flat 302, Lodha Crown
Dhanori, Pune - 411015

📞 Additional Notes (Optional):
[Text area: "Please use the side entrance..."]

Preferred Contact:
☑ WhatsApp: +91 98765 43210
☐ Call
☐ Email

[Back] [Continue] (Primary)
```

### Step 3: Price Breakdown & Summary

```
Price Summary
──────────────

Subtotal:              ₹12,000
Taxes (18% GST):       ₹ 2,160
Delivery Fee:          ₹   200
                       ────────
Total:                 ₹14,360

Available Payment Methods:
☑ Credit/Debit Card
☑ UPI
☑ Wallet
☐ Bank Transfer

[Apply Coupon Code] (link)

[Proceed to Payment] (Primary, full width)
```

### Step 4: Payment Gateway

```
Secure Payment
──────────────

Select Payment Method:
○ Credit Card
○ Debit Card
○ UPI
○ Wallet

├─ Credit Card ──────┐
│ Card Number       │
│ [1234 5678 9012]  │
│ Expiry: MM/YY     │
│ CVV: [***]        │
│ [Confirm Payment] │
└───────────────────┘
```

### Step 5: Booking Confirmation

```
┌─────────────────────────────────────────────┐
│                                             │
│          ✅ Booking Confirmed!              │  ← Confetti animation
│                                             │
│     Your booking has been placed            │
│     successfully!                           │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  Booking ID: #BOOK-20260209-12345          │
│  Reference: Save for your records          │
│                                             │
│  Service: DJ Services                      │
│  Date: Feb 15, 2026                        │
│  Time: 6:00 PM                             │
│  Amount: ₹14,360                           │
│  Status: ✅ Confirmed                      │
│                                             │
├─────────────────────────────────────────────┤
│  Next Steps:                                │
│  → Vendor will contact you within 2 hours  │
│  → View your booking in "My Bookings"      │
│  → Chat with vendor to discuss details     │
│                                             │
│    [Share Booking] [View Details]          │
│    [Go to Home]                    (Primary)
│                                             │
└─────────────────────────────────────────────┘
```

---

## Premium Chat UI

### Chat List Screen

```
┌─────────────────────────────────────────────┐
│ ← Chat       Search [⋮ More]                │
├─────────────────────────────────────────────┤
│                                             │
│ Active Now (3)                              │
│                                             │
│ Avatar Rahul's Catering           🟢 • 2:45│  ← Online indicator
│ "Your order will be delivered by..." |└─────┘  ← Last message
│ 12:45 PM             [Unread count: 3]    │
│                                             │
│ Avatar DJ Mike                    🟡 • 1h  │  ← Away status
│ "Thanks for choosing us! Excited..." |      │
│ Yesterday          05:30 PM                 │
│                                             │
│ Avatar Priya's Decor              🔴 • 3h  │  ← Offline
│ "Sure, let me check with my team..." |      │
│ Feb 5      09:15 AM                        │
│                                             │
├─────────────────────────────────────────────┤
│ Offline                                     │
│                                             │
│ Avatar Green Grocery              🔴 • 1d  │
│ "Thank you for your order!" |              │
│ Feb 4      11:30 AM                        │
│                                             │
│ Avatar Elite Catering             🔴 • 2d  │
│ "Please confirm your guest count" |        │
│ Feb 3      08:00 AM                        │
│                                             │
│ Home │Search │Book │Chat ← │👤              │ [Bottom nav]
└─────────────────────────────────────────────┘
```

### Chat Window

```
┌─────────────────────────────────────────────┐
│ ← Rahul's Catering        🟢 Online         │  [Header: Vendor name + status]
├─────────────────────────────────────────────┤
│                       [Typing indicator...]  │  ← From vendor
│                       Vendor is typing ✏️   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Hi! Your order looks great.         │   │  ← Vendor message (left, gray bg)
│  │ We'll deliver by 6 PM               │   │
│  │ Rahul's Catering  11:23 AM  ✔✔      │   │  ← Name, time, read status
│  └─────────────────────────────────────┘   │
│                                             │
│                ┌──────────────────────┐    │
│                │ Is there a discount  │    │  ← User message (right, primary color)
│                │ for bulk orders?     │    │
│                │    You  11:25 AM  ✔✔ │    │
│                └──────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Yes, absolutely! 15% for orders      │   │
│  │ above ₹5000 🎉                      │   │
│  │ [Image preview] Discount Card.jpg    │   │  ← Shared image
│  │ Rahul's Catering  11:27 AM  ✔       │   │
│  └─────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│ [📎 Attach] [📸 Photo] [😊 Emoji]          │
│ [_____________________________] [Send ➤]   │  ← Message input
└─────────────────────────────────────────────┘
```

**Chat Message Details**
- **Vendor Messages**: Left-aligned, gray background (#F3F4F6), name above
- **User Messages**: Right-aligned, primary color background (#BE185D), white text
- **Timestamps**: Small gray text, right-aligned
- **Read Status**: ✔ (sent), ✔✔ (delivered), ✔✔ (blue, read)
- **Typing Indicator**: Animated dots "Vendor is typing..."
- **File Sharing**: Thumbnail preview for images/documents
- **Online Status**: Green dot in header, "Online" or "Active 2h ago"

---

## Notifications & Alerts

### In-App Bell Notification

```
┌─────────────────────────────────────┐
│ Notifications (3 new)        [✕]    │  ← Card/drawer
├─────────────────────────────────────┤
│                                     │
│ 🟢 ✅ Booking Confirmed             │  ← Green badge
│ Your DJ booking on Feb 15 is done! │
│ Mike's DJ Services • 2 min ago      │
│ [View Booking]                      │
│                                     │
│ 🟡 💬 Vendor Replied                │  ← Orange badge
│ "Sure, we can adjust the timing..."│
│ Catering Express • 5 min ago        │
│ [Open Chat] [Dismiss]              │
│                                     │
│ 🔴 ⚠️ Urgent: Vendor Cancellation   │  ← Red badge, prominent
│ Your dj vendor had an emergency.   │
│ We found a replacement!            │
│ Status: Approved • 10 min ago       │
│ [View Details] [Chat with New DJ]  │
│                                     │
├─────────────────────────────────────┤
│ [Mark All as Read]                  │
│ [Notification Settings]             │
└─────────────────────────────────────┘
```

### Toast Notifications (Bottom Right)

```
✅ Booking added to list       [✕]
────────────────────
(Dismisses auto in 4 seconds)

🔴 ⚠️ Payment Failed           [✕]
────────────────────
Retry payment: [Retry]
```

### Push Notifications (Mobile)

```
💬 New message from Rahul's Catering
"Yes, absolutely! We can adjust the menu..."

[Open]  [Dismiss]
```

---

## Vendor Dashboard

### Overview Screen

```
┌─────────────────────────────────────────────┐
│ Vendor Dashboard    Menu    My Profile    ⚙️ │
├─────────────────────────────────────────────┤
│                                             │
│ 📊 Today's Stats:                           │
│ ┌──────────────────────────────────────┐   │
│ │ Revenue: ₹24,560 ↑ 12% from avg    │   │  ← Premium stat card
│ │ Active Bookings: 5                   │   │
│ │ Pending Quotes: 3                    │   │
│ └──────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│ 📈 Revenue Trend (Last 7 Days)              │  ← Line chart
│ ₹8000 |     ╱╲                             │
│ ₹6000 |    ╱  ╲   ╱                        │
│ ₹4000 |___╱____╲_╱____                     │
│ ₹2000 |                                    │
│     Sun Mon Tue Wed Thu Fri Sat           │
│                                             │
├─────────────────────────────────────────────┤
│ 🔔 Alerts & Pending Actions:                │
│                                             │
│ ⚠️ 1 Quote expiring soon                    │
│    "Sharma's Wedding" - Expires in 2 hours │
│    [Review Quote]                          │
│                                             │
│ ✅ 3 Pending Confirmations                  │
│    [View All]                              │
│                                             │
├─────────────────────────────────────────────┤
│ Quick Actions:                              │
│                                             │
│ [✎ Edit Services] [📋 View Bookings]       │
│ [📅 Calendar] [⚔️ Emergency Cancel]        │
│                                             │
│ Active | Bookings | Quotes | Transactions  │ [Tab bar]
└─────────────────────────────────────────────┘
```

### Bookings Tab

```
Filter: [All] [Upcoming] [Completed] [Cancelled]

Upcoming (8):
──────────────

📌 Feb 15, 2026 - Wedding Reception
   Booking #BOOK-20260215-001
   Client: Priya Singh
   Status: Confirmed ✅
   Amount: ₹47,500
   Time: 6:00 PM - 11:00 PM
   
   [Accept] [Reject] [Chat] [Details]      ← Action buttons
   
   💬 Unread messages: 2


📌 Feb 18, 2026 - Birthday Party
   Booking #BOOK-20260218-002
   Client: Rahul Verma
   Status: Pending Confirmation ⏳
   Amount: ₹15,600
   Time: 7:00 PM onwards
   
   [Accept] [Reject] [Chat] [Details]


Completed (235):
────────────────

✅ Feb 8, 2026 - Corporate Event
   Booking #BOOK-20260208-156
   Client: Acme Corp
   Rating: ⭐⭐⭐⭐⭐ (5.0)
   Amount: ₹68,000
   Earned: ₹68,000 (after commission)
   
   [Rate Client] [View Review]
```

### Emergency Cancellation Flow

```
⚠️ Emergency Cancellation

Are you sure you want to cancel this booking?

Booking: Wedding Reception - Feb 15, 2026
Client: Priya Singh
Amount: ₹47,500

Cancellation Reason (Required):
[✓] Health Emergency
[ ] Vehicle Breakdown
[ ] Staff Unavailability
[ ] Other

Reason Details:
[_________________________________]

Refund Policy:
You will pay the client ₹47,500 + cancellation fee ₹5,000
Your support & reputation will be affected.

[Cancel Booking] (danger/red button)
[Go Back]
```

### After Cancellation Notification

```
🔴 Vendor Cancellation - Alert to Admin

Vendor: Rahul's Catering
Booking: #BOOK-20260215-001
Date: Feb 15, 2026, 6 PM
Client: Priya Singh
Reason: Health Emergency

Status: Admin Notified ✓
Replacement Vendor: Finding automated match...

Client Notification: ✅ Sent
Refund Processing: In Progress
```

---

## Admin Panel

### Dashboard Overview

```
┌─────────────────────────────────────────────┐
│ Admin Panel              Notifications   ⚙️ │
├─────────────────────────────────────────────┤
│                                             │
│ Platform Metrics (Last 30 Days)             │
│ ┌──────────┬──────────┬──────────┐         │
│ │ Revenue  │ Bookings │ Vendors  │         │
│ │ ₹12.4M   │ 4,234    │ 256      │         │
│ │ ↑8.5%    │ ↑12%     │ ↑3.2%    │         │
│ └──────────┴──────────┴──────────┘         │
│                                             │
│ ⚠️ URGENT: 2 Vendor Cancellations          │  ← Alert banner
│   [Review & Assign Replacements]           │
│                                             │
│ 📊 Revenue Chart (30 Days)                  │
│ [Line chart: Showing revenue trend]        │
│                                             │
├─────────────────────────────────────────────┤
│ Navigation:                                 │
│ [Users] [Vendors] [Bookings] [Payments]    │
│ [Disputes] [Analytics] [Settings]          │
└─────────────────────────────────────────────┘
```

### Vendors Management Tab

```
Vendors (256 Total)
Filter: [All] [Active] [Inactive] [Flagged] [Pending Approval]

Search: [Find vendor...] [Advanced Filters]

┌─────────────────────────────────────┐
│ Vendor Name                   Status │
├─────────────────────────────────────┤
│ Rahul's Catering              🟢    │  ← Status indicator
│ Email: contact@rahulcatering... ... │
│ Rating: ⭐ 4.8 (234 reviews) Joined │  ← Meta info
│ Revenue Trend: ↑ 12% | Monthly: ₹42K
│ [Approve] [Suspend] [Details]       │  ← Quick actions
│                                     │
│ Mike's DJ Services            🟢    │
│ Email: mike@djservices...         │
│ Rating: ⭐ 4.9 (412 reviews)       │
│ Revenue Trend: ↑ 8% | Monthly: ₹35K
│ [Approve] [Suspend] [Details]       │
│                                     │
│ Priya's Decor                 🔴    │
│ Email: priya@decorservices...      │
│ Rating: ⭐ 3.2 (45 reviews)        │
│ Status: FLAGGED (2 unresolved disputes)
│ [Review] [Suspend] [Details]        │
│                                     │
│ [Load More]                         │
└─────────────────────────────────────┘
```

### Bookings & Disputes Tab

```
Bookings & Disputes

Pending Actions:
────────────────

🔴 URGENT: Vendor Cancellation
   Booking #BOOK-20260215-001
   Vendor: Rajesh's Entertainment
   Client: Priya Singh
   Date: Feb 15, 2026
   Amount: ₹47,500
   Cancelled Reason: Health Emergency
   
   ✷ Automatic Replacement Suggestions:
   1. Mike's DJ Services (4.9★, Online)
   2. Elite Events DJ (4.7★, Available)
   3. Sound Master (4.5★, Near client)
   
   [Assign #1] [Assign #2] [More Options]
   [Contact Client] [Manual Assignment]


🟡 Payment Dispute
   Booking #BOOK-20260210-045
   Client: Rahul Verma vs DJ Mike
   Issue: "Payment charged twice"
   Amount: ₹5,500
   Status: Waiting for vendor response
   
   [Chat History] [Resolve] [Refund]


✅ Completed (234 this month)
   [View All]
```

### Replacement Assignment Modal

```
┌────────────────────────────────────────┐
│ Assign Replacement Vendor              │  XXX ← Close button
├────────────────────────────────────────┤
│                                        │
│ Original Booking:                      │
│ Vendor: Rajesh's Entertainment         │
│ Service: Wedding DJ                    │
│ Date: Feb 15, 2026 @ 6 PM             │
│ Client: Priya Singh                    │
│ Location: Pune, Koregaon Park          │
│                                        │
├────────────────────────────────────────┤
│ Replacement Suggestions (AI-Matched):  │
│                                        │
│ ✓ Mike's DJ Services                  │  ← Selected (checked)
│   Rating: ⭐⭐⭐⭐⭐ (4.9, 412 reviews)   
│   Availability: ✅ Available           │
│   Distance: 2.3 km                     │
│   Response Time: Usually <30 min       │
│   Pricing: ₹3,500/hour (Match) 100%   │
│                                        │
│ Elite Events DJ                       │
│   Rating: ⭐⭐⭐⭐ (4.7, 189 reviews)    
│   Availability: ✅ Available           │
│   Distance: 4.1 km                     │
│   Response Time: Usually <1 hour       │
│   Pricing: ₹3,200/hour (Save 8%)      │
│                                        │
│ [View Full Profile] [Contact]         │
│                                        │
├────────────────────────────────────────┤
│                                        │
│ Refund Method:                         │
│ ○ Full Refund to Client               │
│ ○ Credit towards next booking         │
│                                        │
│ [Assign & Notify] [Cancel Assignment] │
│                                        │
└────────────────────────────────────────┘
```

---

## Emergency Vendor Cancellation UX

### User Sees (Notification Timeline)

```
Timeline:

T+0 min:
┌─────────────────────────────────────────────┐
│ 🔴 ALERT: Vendor Issue                      │
│                                             │
│ We're arranging a replacement vendor        │
│                                             │
│ Your DJ booking on Feb 15 has an issue.     │
│ Rajesh has had an emergency.                │
│                                             │
│ ✓ Status: Replacement being arranged       │
│ ⏳ ETA: Within 2 hours                      │
│                                             │
│ [View Details] [Chat with Admin] [Call]    │
└─────────────────────────────────────────────┘

T+30 min:
┌─────────────────────────────────────────────┐
│ ✅ Resolution Update                        │
│                                             │
│ We found Mike's DJ Services!                │
│                                             │
│ Same quality, same timeline, same budget    │
│                                             │
│ Mike's DJ Services:                         │
│ ⭐ 4.9/5 (412 reviews)                     │
│ Available: ✅ Yes                          │
│ Price: ₹3,500/hour (Same)                  │
│                                             │
│ [Accept Replacement] [Different DJ]        │
├─────────────────────────────────────────────┤
│ Refund Guarantee:                           │
│ If you're not satisfied, 100% refund       │
│ No questions asked!                        │
│                                             │
│ [Accept]                            (green) │
└─────────────────────────────────────────────┘

T+60 min:
┌─────────────────────────────────────────────┐
│ ✅ Issue Resolved!                          │
│                                             │
│ Mike's DJ Services has accepted your        │
│ booking for Feb 15, 6 PM.                   │
│                                             │
│ Next Step: Chat with Mike to discuss       │
│ your preferences & requirements!           │
│                                             │
│ [Chat with Mike] [View Details]            │
│ [Rate Resolution]                          │
│                                             │
│ Your satisfaction is our priority!         │
└─────────────────────────────────────────────┘
```

### Admin Dashboard View

```
🔴 URGENT - Vendor Cancellation
─────────────────────────────
Booking: #BOOK-20260215-001
Vendor: Rajesh's Entertainment
Client: Priya Singh
Status: ACTIVE INCIDENT

Timeline:
─────────
12:45 PM - Vendor reported emergency
12:46 PM - Auto-match initiated (3 candidates selected)
12:50 PM - Mike's DJ accepted (First match accepted!)
12:52 PM - Client notified via SMS + In-app
01:05 PM - Client accepted replacement
01:07 PM - New vendor (Mike) contacted client

Status: ✅ RESOLVED (Time taken: 22 minutes)

[View Full Incident Report] [Feedback] [Archive]
```

---

## Micro-Interactions

### 1. Button Interactions

**Primary CTA Button**
```
Default:
[Add to Booking]
Dark rose, shadow, rounded

Hover:
[Add to Booking]
Lighter rose, larger shadow, translateY(-2px)

Active/Click:
[Add to Booking]
Darker rose, no shadow offset, translateY(0)
Ripple effect extends outward (light rose, fading)

Disabled:
[Add to Booking]
Gray, opacity 0.6, no cursor interaction
```

**Micro-animation of successful action:**
```
1. Ripple effect (100ms)
2. Button text changes to checkmark (150ms fade-in)
3. Button color changes to green (#10B981) (200ms)
4. Toast notification appears (250ms slide-up)
5. Button resets to normal state after 2 seconds
```

### 2. Page Transitions

- **Slide Left**: New page enters from right, old page exits left (250ms, ease-out)
- **Fade + Scale**: Elements fade in while scaling up 95% → 100% (200ms)
- **Stagger Animation**: List items animate in sequentially (50ms delay each)

### 3. Loading States

**Skeleton Loading**
```
┌──────────────────────────┐
│ ▓▓▓▓▓▓▓ (animated shimmer)│  ← Vendor name placeholder
│ ▓▓▓▓ ▓▓▓ (animated)       │  ← Rating placeholder
│ ▓▓▓▓▓▓▓▓▓▓▓ (animated)    │  ← Price placeholder
└──────────────────────────┘
(Shimmer moves left→right at 1.5px/ms)
```

### 4. Confirmation & Success Animations

**Booking Confirmation**
1. Confetti animation (particles fall randomly, fade out at bottom)
2. Checkmark circle grows from center (0→100px, 300ms)
3. Page content fades in after 500ms
4. Success sound plays (optional, muted by default)

**Quantity Selector**
```
Current: 2 kg

User taps [+]:
  1. Button flashes
  2. Number increases (brief scale 1.2x)
  3. Subtotal updates with color flash
  4. Haptic feedback (mobile)
  5. Smooth animation (all 200ms ease-out)
```

### 5. Chat Typing Indicator

```
Animated dots:
●  ●  ●
(Each dot bounces up-down in sequence)
"Vendor is typing..."
Animation: 600ms cubic-bezier(0.4, 0, 0.2, 1)
```

### 6. Notification Appearance

**Toast Slide In**
```
Initial: Position off-screen bottom (0, height+20)
Slide in: 0, 0 (250ms ease-out)
Hold: 3000ms
Slide out: 0, height+20 (200ms ease-in)
```

### 7. Hover Effects on Cards

```
Vendor Card:
  Default: 
    - Shadow: md
    - Transform: none
    - Opacity: 1
  
  Hover:
    - Shadow: lg (smoothly transitions 150ms)
    - Transform: translateY(-4px) (smooth 150ms)
    - Opacity: 1
    - Background faint overlay (10% dark, 150ms fade-in)
  
  Transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1)
```

### 8. Accordion Expand/Collapse

```
Collapsed:
▶ Rice (12 items)

User clicks:
1. Chevron rotates 0° → 90° (200ms)
2. Content height expands (contentHeight, 300ms ease-out)
3. Opacity fade-in for items (0.5 → 1.0, staggered)
4. Bottom margin increases (200ms)

Expanded:
▼ Rice (12 items)
  [Item 1]  [Item 2]  [Item 3]
  [Item 4]  [Item 5]  [Item 6]
```

---

## Responsive Design

### Breakpoints

| Device | Width | Layout |
|--------|-------|--------|
| Mobile | < 768px | Single column, bottom tabs |
| Tablet | 768px - 1024px | 2 columns, sidebar drawer |
| Desktop | > 1024px | Sidebar + main content (multi-column) |

### Mobile-First Adjustments

**Home Screen (Mobile)**
- Hero: 200px height (vs 300px desktop)
- Vendor cards: Full width - 2 columns layout
- Quick action cards: 4 in a row, swipe-able
- Bottom navigation: Fixed, sticky

**Vendor Listing (Mobile)**
- Full-width vendor cards (1 column)
- Filter as bottom sheet (swipe up)
- Sticky search at top
- Infinite scroll (vs pagination)

**Vendor Detail (Mobile)**
- Image carousel: Full-width, swipe to navigate
- Tabs: Horizontal scroll (sticky)
- Sticky bottom CTA (Book Now button)
- Services info: Accordion expand for readability

**Chat (Mobile)**
- Full screen message area
- Sticky input at bottom (accounts for keyboard)
- Avatar: Smaller (32px vs 48px desktop)
- Message bubbles: Full width (with padding)

### Desktop-First Adjustments

**Multi-column Layouts**
- Vendor listing: 3-4 columns per row
- Services: Side-by-side layout (left: items, right: summary)
- Chat: Split-screen (left: chat list 280px, right: message area)

**Navigation**
- Sidebar always visible (not hamburger)
- Horizontal tabs instead of swipeable
- Hover states more pronounced

---

## Color Application Guide

### Where Each Color Goes

| Color | Primary Use | Hex |
|-------|------------|-----|
| Deep Rose | CTAs, primary focus, headers, active states | #BE185D |
| Charcoal | Body text, secondary elements, dark UI | #1F2937 |
| Gold | Highlights, ratings, premium badges, accents | #F59E0B |
| Soft White | Backgrounds, cards, light surfaces | #FAFAFA |
| Gray | Borders, secondary text, disabled states | #D1D5DB - #6B7280 |
| Green | Success, positive actions, checkmarks | #10B981 |
| Red | Errors, cancellations, urgent alerts | #EF4444 |
| Blue | Info, secondary CTAs, notifications | #3B82F6 | 

---

## Implementation Priority

### Phase 1 (MVP - Week 1-2)
✅ Design system tokens (colors, typography, spacing)
✅ Button components (primary, secondary, icon variants)
✅ Card components
✅ Input components
✅ Home page layout
✅ Vendor listing page structure

### Phase 2 (Core Features - Week 3-4)
⏳ Vendor detail page with tabs
⏳ Dynamic services UI (start with grocery)
⏳ Booking flow (4 steps)
⏳ Chat interface
⏳ Basic notifications

### Phase 3 (Polish & Advanced - Week 5-6)
⏳ Micro-animations
⏳ Responsive refinements
⏳ Vendor dashboard
⏳ Admin panel
⏳ Emergency cancellation flows
⏳ Advanced chat features (typing indicator, read status)

### Phase 4 (Premium Polish - Week 7+)
⏳ Confetti animations
⏳ Advanced micro-interactions
⏳ Haptic feedback (mobile)
⏳ Performance optimizations
⏳ Accessibility audit & improvements

---

## Accessibility Guidelines

- All buttons: Min 48px touch target (mobile)
- Color contrast: WCAG AA (4.5:1 for text)
- Focus states: Visible focus rings (2px primary color)
- Icons: Always paired with text labels (or aria-label)
- Form labels: Associated with inputs (label htmlFor)
- Navigation: Semantic HTML (nav, main, aside)
- Images: Descriptive alt text
- Modals: Trap focus, ARIA attributes
- Links: Underline or clear visual distinction

---

## CSS Architecture Recommendation

```
src/
├── styles/
│   ├── tokens/
│   │   ├── colors.css
│   │   ├── typography.css
│   │   ├── spacing.css
│   │   └── shadows.css
│   ├── base/
│   │   ├── reset.css
│   │   ├── typography.css
│   │   └── global.css
│   ├── components/
│   │   ├── button.css
│   │   ├── card.css
│   │   ├── input.css
│   │   ├── badge.css
│   │   └── ...
│   ├── layouts/
│   │   ├── sidebar.css
│   │   ├── grid.css
│   │   └── spacing.css
│   ├── utilities/
│   │   ├── flexbox.css
│   │   ├── grid.css
│   │   ├── text.css
│   │   └── ...
│   └── themes/
│       └── colors.css
└── components/
    ├── Button/
    ├── Card/
    ├── Input/
    └── ...
```

---

## Next Steps for Implementation

1. **Create Design System Component Library** (React)
   - Export all button variants, colors, spacing scales
   - Storybook integration for component showcase

2. **Build Base Layouts**
   - Mobile bottom tab navigation
   - Web sidebar navigation
   - Responsive grid system

3. **Implement Page Templates**
   - Home page
   - Vendor listing
   - Vendor detail
   - Booking flow

4. **Add Interactive Features**
   - Chat UI with real-time messages
   - Notifications system
   - Micro-animations

5. **Vendor Dashboard**
   - Booking management
   - Stats & revenue tracking
   - Emergency cancellation flow

6. **Admin Panel**
   - Vendor management
   - Booking oversight
   - Automated replacement assignment

---

**Design System Version: 1.0**  
**Last Updated: February 9, 2026**  
**Status: Ready for Implementation**
