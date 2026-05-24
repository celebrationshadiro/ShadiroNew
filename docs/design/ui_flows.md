# 🎬 Shadiro UI Flows & Screen Mapping
## Complete User Journey • Vendor Registration • Category Logic • Booking Flows

---

## 📱 Screen List by Feature

### Total Screens to Build: 45+
```
Authentication:         6 screens (sign up, login, forgot password, verification)
Onboarding:            4 screens (user type, preferences, tutorial)
Landing & Explore:     5 screens (home, search, filters, category browse, trending)
Vendor Business:       8 screens (registration, dashboard, listings, analytics)
Discovery & Comparison: 4 screens (listing, detail, comparison, reviews)
Chat & Quotes:         3 screens (chat list, chat detail, quote review)
Booking & Checkout:    5 screens (packages, add-ons, checkout, payment, confirmation)
Post-Booking:          4 screens (dashboard, timeline, invoice, support)
Admin:                 3 screens (dashboard, moderation, vendor management)
Settings & Profile:    3 screens (profile, preferences, notifications)
```

---

## 🏠 USER FLOWS

### Flow 1: New User → First Booking (Happy Path)

```
Start: Landing Page
  ↓
  [Sign Up / Login]
  ├─ Phone number (OTP verification)
  ├─ Name & email
  ├─ Set preferences (event type, budget, date)
  └─ Done (push to Home)
  ↓
Home Page
  ├─ Featured vendors carousel
  ├─ Personalized recommendations banner
  ├─ Recent searches shortcut
  ├─ Bottom nav: Home | Explore | Wishlist | Bookings | Profile
  └─ CTA: "Plan My Event" or "Browse Vendors"
  ↓
Explore / Category Browse
  ├─ Category grid: Venues, Caterers, Decorators, etc.
  ├─ Advanced filters (expandable sheet):
  │  ├─ Budget range slider
  │  ├─ Location (map radius)
  │  ├─ Availability dates
  │  ├─ Rating filter
  │  └─ Verification status
  └─ Listing displayed (grid or list toggle)
  ↓
Vendor Detail Page
  ├─ Hero image carousel (swipe-able)
  ├─ Vendor info header:
  │  ├─ Name, category, location
  │  ├─ Rating (4.8 ⭐ 328 reviews)
  │  ├─ Verification badge ✓
  │  ├─ Featured tag (if applicable)
  │  └─ Response time ("2 hours avg")
  ├─ Tabs: Overview | Packages | Items | Reviews | About
  ├─ Overview:
  │  ├─ Short description
  │  ├─ Key highlights (experience, specializations)
  │  ├─ Pricing info ("Starting from ₹5,000")
  │  └─ Availability check (green = available)
  ├─ Packages Tab:
  │  ├─ Card per package
  │  ├─ Name, price, what's included
  │  └─ "Select this package" CTA
  ├─ Items Tab:
  │  ├─ Accordion per category
  │  ├─ Example (DJ): Speakers, lights, DJ trolley, backup power
  │  ├─ Quantity selector for each item
  │  └─ Add items to cart
  ├─ Reviews Tab:
  │  ├─ Star breakdown (5★, 4★, 3★, etc.)
  │  ├─ Filter by star rating
  │  ├─ Sort by recent / helpful
  │  └─ Latest 5 reviews with photos
  ├─ About Tab:
  │  ├─ Experience summary
  │  ├─ Cancellation policy
  │  ├─ Service area
  │  └─ "Contact vendor" option
  └─ Sticky CTA: "Request Quote" or "Select Package & Checkout"
  ↓
Chat / Quote Request
  ├─ Display selected package/items
  ├─ Message field: "Add any special requests..."
  ├─ Show price summary (package + selected items + taxes)
  ├─ CTA: "Send Quote Request"
  └─ Toast: "Quote request sent! Vendor usually responds in 2 hours"
  ↓
Chat Interface (WhatsApp-Style)
  ├─ Vendor profile header (name, rating, response time)
  ├─ Conversation thread (timestamped messages)
  ├─ Vendor sends: Quote details + customization options
  ├─ User reviews: Accept, decline, or request changes
  ├─ Message input + attachment (photo) support
  ├─ Inline actions: "Accept Quote", "Make Payment", "Chat"
  └─ Show: Vendor is typing...
  ↓
Checkout Flow (4 Steps)
  ├─ Step 1: Review & Confirm
  │  ├─ Display: Event date, guest count, location
  │  ├─ Display: Selected package + items + pricing
  │  ├─ Total amount (with breakdown: goods, taxes, Shadiro fee)
  │  └─ CTA: "Continue to Payment"
  ├─ Step 2: Payment Method
  │  ├─ Card entry (with card icons for Visa, MC, Amex)
  │  ├─ UPI option (popular in India)
  │  ├─ Wallet options
  │  ├─ "Secure payment powered by [provider]" badge
  │  └─ Promo code field (optional)
  ├─ Step 3: Booking Summary
  │  ├─ Vendor name, date, time
  │  ├─ Total amount with breakdown
  │  ├─ Cancellation policy link
  │  ├─ "Booking protected with Shadiro Shield" message
  │  └─ Checkbox: Agree to terms
  └─ Step 4: Confirmation
     ├─ Green success page
     ├─ Booking ID, receipt link
     ├─ Next steps: "Chat with vendor", "View timeline"
     ├─ Calendar add (Google, Apple)
     └─ Share confirmation with family
  ↓
Booking Dashboard
  ├─ Booking card showing:
  │  ├─ Vendor name + image
  │  ├─ Event date, time, location
  │  ├─ Amount paid
  │  ├─ Status badge (Green: Confirmed)
  │  ├─ Countdown to event
  │  └─ Quick actions: Chat, View details, Invoice
  ├─ Event Timeline (visual phases)
  └─ CTA: "Invite others to this event"
```

### Flow 2: Search & Compare (Discovery)

```
Start: Explore Page
  ↓
Search/Filter
  ├─ Category: Select "Caterers"
  ├─ Location: Delhi (with map radius)
  ├─ Budget: ₹20,000 - ₹50,000
  ├─ Availability: March 30, 2026
  ├─ Verification: Only show verified vendors
  ├─ Sort by: "Recommended" (default)
  └─ Results: 28 matching vendors
  ↓
Listing Page
  ├─ Grid layout (2 columns on mobile, 4 on desktop)
  ├─ Vendor cards showing:
  │  ├─ Hero image
  │  ├─ Verification badge (top-right corner)
  │  ├─ Name + category icon
  │  ├─ Location (city)
  │  ├─ Rating + review count
  │  ├─ Price range ("From ₹25,000")
  │  └─ "Add to compare" checkbox (in card corner)
  ├─ Sticky toolbar (when scrolling):
  │  ├─ "Showing 28 results"
  │  ├─ Filter button (re-open filters)
  │  ├─ Sort dropdown
  │  └─ "Compare selected (3)" button (appears when cards selected)
  └─ Tap on card → Vendor detail
  ↓
Add to Compare (User selected 3 vendors)
  ├─ Checkbox on each card visually selected
  ├─ Toast: "Added to comparison (3 vendors)"
  └─ Sticky CTA: "Compare 3 vendors" (blue)
  ↓
Comparison Page
  ├─ Desktop: Table view
  │  ├─ Columns: Vendor name | Rating | Price | Experience | Featured
  │  ├─ Rows: Each metric for comparison
  │  └─ Sticky column: Vendor name (scroll right)
  ├─ Mobile: Card view
  │  ├─ Carousel of vendor cards
  │  ├─ Each card shows: Image, name, rating, price
  │  ├─ Horizontal scroll to view all vendors
  │  └─ Swipe to see next vendor
  ├─ Metrics:
  │  ├─ Name & category
  │  ├─ ⭐ Rating + review count
  │  ├─ 💰 Price range / starting price
  │  ├─ 📅 Availability for your date (✓ or ✗)
  │  ├─ 🏅 Experience (years)
  │  ├─ ✓ Verified status
  │  ├─ ⭐ Featured tag (if applicable)
  │  └─ 📍 Service area
  ├─ Actions (per vendor column):
  │  ├─ "View Details" button
  │  ├─ "Request Quote" button
  │  └─ "Add to Wishlist" heart icon
  └─ Remove vendor: Edit comparison, deselect vendors
```

---

## 🔐 AUTHENTICATION FLOWS

### Sign Up Flow (New User)

```
Landing Page
  ↓
Tap "Sign up" or "Continue as Customer"
  ↓
Phone Verification Screen
├─ Title: "Let's verify your phone number"
├─ Input: Phone number with country code (+91 India)
├─ Checkbox: "I agree to terms & privacy"
└─ CTA: "Send OTP"
  ↓
OTP Verification
├─ Title: "Enter OTP sent to [phone]"
├─ 6-digit input fields (auto-focus after input)
├─ Countdown timer: "Resend OTP in 30s"
├─ Link: "Wrong number? Change it"
└─ CTA: "Verify & Continue"
  ↓
Profile Setup
├─ Name input (first + last)
├─ Email input (optional but recommended)
├─ Location preference (city selector)
├─ Event type preference (Wedding, Corporate, Birthday, etc.)
├─ Budget range (slider: ₹50k - ₹100L)
└─ CTA: "Complete Sign Up"
  ↓
Welcome Screen
├─ Green checkmark
├─ "Welcome, [Name]!"
├─ "Your preferences are set"
├─ Next: Explore vendors or Plan my event
└─ CTA: "Let's Find Vendors"
  ↓
Home Page
```

### Vendor Sign Up Flow

```
Landing Page
  ↓
Tap "Register as Vendor"
  ↓
Business Type Selection
├─ Category grid: "Choose your service category"
├─ Options:
│  ├─ 🏛️ Event Venues
│  ├─ 👰 Wedding Planners
│  ├─ 💄 Makeup Artists & Stylists
│  ├─ 📸 Photographers & Videographers
│  ├─ 🎀 Decorators & Florists
│  ├─ 🍽️ Caterers & Bakers
│  ├─ 🎵 DJs, Bands & Entertainers
│  ├─ 🚗 Transport & Rental Services
│  └─ 🎨 Mehandi Designers
└─ Select one → Next
  ↓
Business Details (Category-Specific Form)
├─ Common fields:
│  ├─ Business name
│  ├─ Phone number (for vendor contact)
│  ├─ Email
│  ├─ Location (city + service area radius)
│  ├─ Experience (years in business)
│  └─ Number of events completed
├─ Category-specific examples:
│  ├─ VENUE:
│  │  ├─ Venue type (banquet hall, resort, garden)
│  │  ├─ Capacity (min - max guests)
│  │  ├─ Price per plate
│  │  ├─ Available facilities (parking, AC, decoration space)
│  │  └─ Meal provided? (Yes/No)
│  ├─ CATERER:
│  │  ├─ Cuisine types (North Indian, South Indian, Chinese, Continental, Fusion)
│  │  ├─ Specialization (veg, non-veg, both)
│  │  ├─ Price per plate range
│  │  ├─ Min guests requirement
│  │  └─ Services: Menu planning, food prep, service, cleanup
│  └─ DECORATOR:
│     ├─ Specialization (theme, color, style)
│     ├─ Price per sq ft
│     ├─ Services (stage, entrance, dining, mehandi)
│     └─ Materials sourced (local, imported)
└─ CTA: "Next Step"
  ↓
Media Upload
├─ Upload profile photo (business logo or owner)
├─ Upload portfolio images (min 5, max 20):
│  ├─ Drag-drop upload
│  ├─ Crop & arrange images
│  └─ "Add labels" optional (e.g., "Wedding of Mr. & Mrs. XYZ")
├─ Video intro (optional, 15-30s max)
└─ CTA: "Continue"
  ↓
Pricing & Packages
├─ Title: "Set your pricing"
├─ Package structure (3 tiers):
│  ├─ Basic Package
│  │  ├─ Name: "Essential"
│  │  ├─ Price: [input]
│  │  ├─ What's included: [textarea]
│  │  └─ Customizable: Yes/No
│  ├─ Standard Package
│  │  ├─ Name: "Premium"
│  │  ├─ Price: [input]
│  │  ├─ What's included: [textarea]
│  │  └─ Customizable: Yes/No
│  └─ Premium Package
│     ├─ Name: "Luxury"
│     ├─ Price: [input]
│     ├─ What's included: [textarea]
│     └─ Customizable: Yes/No
├─ Add-ons section:
│  ├─ Additional service name + price
│  ├─ "Add another add-on" button
│  └─ Up to 10 add-ons
└─ CTA: "Save Packages"
  ↓
Availability Calendar
├─ Monthly calendar
├─ Select available dates (at least 7 days)
├─ Multiple selection allowed
├─ Show as: "Available", "Booked", "On Holiday"
├─ Set buffer time (no bookings within X days of booking)
└─ CTA: "Save Availability"
  ↓
Review & Submit
├─ Summary of all entered data
├─ Sections: Category, Business Info, Media, Pricing, Availability
├─ Edit button on each section
├─ T&C checkbox: Agree to vendor terms
└─ CTA: "Submit for Verification"
  ↓
Verification Pending
├─ Screen: "Thank you for registering!"
├─ Message: "Your profile is under review. Usually takes 24-48 hours."
├─ Next steps: "Check dashboard for updates"
└─ Meanwhile: "Complete your profile (x% complete)" section
  ↓
Email Confirmation
├─ Email: "Welcome to Shadiro! Your profile is under review."
├─ When approved: "Your profile is live! Start getting bookings!"
└─ Vendor DashboardEmail confirmation sent (start accepting bookings)
```

---

## 🎯 VENDOR CATEGORY LOGIC

### Dynamic Form Structure (Based on Category)

#### Example 1: CATERER/BAKER

```
Business Details
├─ Business name
├─ Cuisine types (multi-select):
│  ├─ North Indian
│  ├─ South Indian
│  ├─ Chinese
│  ├─ Continental
│  ├─ Fusion
│  ├─ Desserts & Baked
│  └─ Beverages
├─ Dietary options:
│  ├─ Vegetarian
│  ├─ Non-vegetarian
│  ├─ Vegan
│  └─ Gluten-free
├─ Minimum guests requirement: [number]
├─ What's included in service:
│  ├─ Menu planning & consultation
│  ├─ Food preparation
│  ├─ Plating & presentation
│  ├─ On-site serving & buffet setup
│  ├─ Cleanup & dishwashing
│  └─ Chauffer & transport (optional)
├─ Liquor policy (BYOB, provide, not allowed)
└─ Price per plate range: ₹[min] - ₹[max]

Packages
├─ Package 1: "Basic Spread"
│  ├─ Price: ₹350/plate
│  ├─ Includes: 20 items (3 curries, rice, 2 breads, salad, dessert, beverages)
│  └─ Service: Self-service buffet
├─ Package 2: "Premium Catering"
│  ├─ Price: ₹600/plate
│  ├─ Includes: 30 items (5 curries, rice, 3 breads, salads x2, 2 desserts, beverages)
│  └─ Service: Plated service + bartender
└─ Package 3: "Luxury Experience"
   ├─ Price: ₹1200/plate
   ├─ Includes: 40+ items (custom menu, pre-dinner cocktails, wine pairing)
   └─ Service: Full service with sommelier

Add-ons
├─ Extra vegetable dishes: +₹100/plate
├─ Premium desserts: +₹150/plate
├─ Alcohol service (beer/cocktails): +₹200/plate
├─ Live cooking station: +₹5000 flat
├─ Professional bartender: +₹3000 per event
└─ Cleanup crew (4 people): +₹4000 per event

Items Catalog (In Vendor Dashboard)
├─ Each item is:
│  ├─ Name (e.g., "Butter Chicken")
│  ├─ Cuisine type
│  ├─ Category: Vegetarian / Non-veg / Dessert / Beverage
│  ├─ Description
│  ├─ Photo
│  ├─ Unit: Per plate / Per portion / Per liter
│  ├─ Price
│  └─ Allergen info
├─ Customers can:
│  ├─ View available items
│  ├─ Add items to their booking
│  ├─ Customize menu (request items not listed)
│  └─ View item photos in detail
```

#### Example 2: DJ / ENTERTAINER

```
Business Details
├─ Business name
├─ Specializations (multi-select):
│  ├─ Wedding Receptions
│  ├─ Mehandi / Sangeet
│  ├─ Corporate Events
│  ├─ Birthday Parties
│  ├─ Engagement Parties
│  ├─ Cocktail Parties
│  └─ New Year / Community Events
├─ Languages: Hindi, English, Punjabi, Tamil, Telugu, etc.
├─ Equipment owned:
│  ├─ Main sound system (power output)
│  ├─ Microphones (#)
│  ├─ Lights / LED
│  ├─ Projector & DJ screen
│  ├─ Fog machine
│  └─ Backup generator
├─ Experience (years)
└─ Venue size they can handle: (min - max sq ft)

Packages
├─ Package 1: "DJ Only"
│  ├─ Price: ₹15,000
│  ├─ Includes: DJ + sound system + basic lighting
│  ├─ Duration: 4 hours
│  └─ Includes: Song requests, MC services, dance floor setup
├─ Package 2: "Complete Entertainment"
│  ├─ Price: ₹30,000
│  ├─ Includes: DJ + professional sound + LED lights + projector + games
│  ├─ Duration: 5 hours
│  └─ Includes: MC services, dance floor management, photo backdrop
└─ Package 3: "Premium Show"
   ├─ Price: ₹50,000
   ├─ Includes: DJ + band + production + lights + fog + special effects
   ├─ Duration: 6 hours
   └─ Includes: Custom choreography, pyrotechnics, celebrity appearances available

Items / Equipment (Rental)
├─ DJ equipment:
│  ├─ Additional microphone: +₹2,000
│  ├─ Wireless microphone: +₹3,000
│  ├─ Professional lights (per set): +₹5,000
│  ├─ LED screen (per sq meter): +₹500
│  ├─ Fog machine: +₹2,000
│  ├─ Bubble machine: +₹1,000
│  └─ Backup power supply: +₹3,000
├─ Specialties:
│  ├─ Live band feature: +₹20,000
│  ├─ Singer performance: +₹15,000
│  ├─ Dancers for opening act: +₹10,000
│  └─ Special visual effects (fireworks, etc.): Quoted separately

Availability Features
├─ Multi-day bookings (Mehandi, Sangeet, Wedding)
├─ Break between events minimum: 2 days
├─ Travel distance (how far they go): 50km radius
└─ On-site setup time: 2-3 hours before event

Vendor Dashboard Items
├─ Manage song library/playlist
├─ Save customer preferences
├─ Track equipment availability
├─ Manage backup equipment
└─ View real-time event timeline
```

#### Example 3: DECORATOR / FLORIST

```
Business Details
├─ Business name
├─ Decoration styles (multi-select):
│  ├─ Theme Based (Vintage, Bohemian, Royal, Modern, Minimalist)
│  ├─ Floral Heavy (Flowers + drapes)
│  ├─ Carpet & Lighting (Budget-friendly)
│  ├─ Stage setups
│  ├─ Entrance & backdrop decoration
│  ├─ Table centerpieces
│  └─ Wedding favors
├─ Flower sourcing:
│  ├─ Fresh imported flowers
│  ├─ Local seasonal flowers
│  ├─ Artificial flowers (premium, preserved)
│  └─ Locally sourced budget option
├─ Services offered:
│  ├─ Concept & design
│  ├─ 3D visualization
│  ├─ Decoration setup
│  ├─ Mehandi/Sangeet stage
│  ├─ Wedding mandap
│  ├─ Dining table decor
│  ├─ Entrance & photo booth
│  └─ Event branding (logos, monograms, backdrops)
├─ Material sourcing (% they provide, % client provides)
├─ Price per sq ft: [range]
└─ Hidden charges: Specify any (travel, labor, waste)

Packages
├─ Package 1: "Essential Decor"
│  ├─ Price: ₹30,000 - ₹50,000
│  ├─ Includes: Basic theme, flowers for entrance & stage
│  ├─ Coverage: 1000 sq ft
│  └─ Duration: 1 day (8 hours setup + decoration)
├─ Package 2: "Premium Decoration"
│  ├─ Price: ₹80,000 - ₹1.5L
│  ├─ Includes: Full-scale theme, flowers, lighting, drapes, ceilings
│  ├─ Coverage: 2000 sq ft (multiple areas)
│  └─ Duration: Multi-day (Mehandi + Wedding + Reception)
└─ Package 3: "Luxury Wedding"
   ├─ Price: ₹2L+
   ├─ Includes: Custom design, imported flowers, full production
   ├─ Coverage: 5000+ sq ft
   └─ Duration: Full wedding (3-4 days)

Items / Services Catalog
├─ Floral arrangements:
│  ├─ Entrance arch (designer): ₹50,000 - ₹150,000
│  ├─ Mandap flowers: ₹2,00,000 - ₹5,00,000
│  ├─ Table centerpieces (per table): ₹5,000 - ₹20,000
│  ├─ Bouquets for bride/groom: ₹10,000 - ₹50,000
│  └─ Flower petals/garlands: ₹2,000 - ₹5,000
├─ Non-flower decor:
│  ├─ Drapes (per running meter): ₹500 - ₹2,000
│  ├─ Lighting (per point): ₹5,000 - ₹20,000
│  ├─ Custom backdrops: ₹15,000 - ₹50,000
│  ├─ Table linens: ₹500 - ₹2,000 per table
│  └─ Carpet (per sq ft): ₹20 - ₹100
├─ Labor charges:
│  ├─ Decoration setup: ₹500/sq ft or flat rate
│  ├─ Designer consultation: ₹5,000 - ₹20,000
│  └─ 3D visualization: ₹2,000 - ₹5,000

Availability & Logistics
├─ Can do multiple days: Yes/No
├─ Setup time required: X hours before event
├─ Breakdown time: X hours after event
├─ Payment terms: % advance, % on day, % after
└─ Cancellation policy: [custom text]
```

#### Example 4: VENUE (Event Venue)

```
Venue Details
├─ Venue type:
│  ├─ Banquet Hall
│  ├─ Resort/Hotel
│  ├─ Farm House
│  ├─ Heritage Property
│  ├─ Open Ground
│  ├─ Club
│  └─ Garden/Outdoor
├─ Total capacity (min - max guests)
├─ Indoor area: [sq ft]
├─ Outdoor area: [sq ft]
├─ Parking capacity: [number]
├─ Parking charges: Free / ₹[amount] per vehicle
├─ Event types supported:
│  ├─ Wedding
│  ├─ Mehandi
│  ├─ Sangeet
│  ├─ Reception
│  ├─ Bachelor party
│  ├─ Corporate events
│  └─ Birthday parties

Facilities & Amenities
├─ Air conditioning
├─ Heater
├─ Sound system
├─ Stage & lighting
├─ Kitchen facilities
├─ Separate bar
├─ Washroom facilities
├─ Wheelchair accessible
├─ Decoration allowed: Yes/No (restrictions)
├─ Outside decoration: Yes/No
├─ Own catering only: Yes/No (or allow external catering)
└─ Liquor license: Yes/No

Packages
├─ Package 1: "Hall Rental Only"
│  ├─ Price: ₹1,00,000 (per day)
│  ├─ Includes: Hall + tables + chairs + basic plates/cutlery
│  ├─ Duration: 12 hours
│  └─ Capacity: Up to [X] guests
├─ Package 2: "Full Catering Package"
│  ├─ Price: ₹500/plate minimum 300 guests
│  ├─ Includes: Hall + catering + service + decoration space
│  ├─ Duration: 5 hours
│  └─ Meal options: 3 menus to choose from
└─ Package 3: "Wedding Package (Multi-Day)"
   ├─ Price: ₹5,00,000 (Mehandi + Sangeet + Wedding + Reception)
   ├─ Includes: All halls + seating + decoration support
   ├─ Duration: 3 days
   └─ Includes: Staff, parking, security

Add-ons / Extra Services
├─ Extra time (per hour): ₹[amount]
├─ Catering (per plate, external vendor): ₹[amount]
├─ Decoration package (includes venue coordination): ₹[amount]
├─ Security staff (per person per day): ₹[amount]
├─ Parking validation (per vehicle): ₹[amount]
├─ Photography permission: Free/Charged
├─ Videography permission: Free/Charged
└─ Bar setup: Free/Charged

Special Features
├─ Kitchen available for vendor use
├─ Multiple separate rooms
├─ Can accommodate both indoor & outdoor events simultaneously
├─ Bridal suite availability
├─ Guest accommodation nearby
└─ Event coordination team available

Availability Setup
├─ Multi-day bookings (show as blocks on calendar)
├─ Setup/breakdown time (specify hours)
├─ Buffer time between events: [hours]
├─ Blocked dates (maintenance, private events): [dates]
└─ Peak season surcharge: [%]

Vendor Dashboard
├─ Booking calendar (color-coded by status)
├─ Event timeline (what happens each day)
├─ Guest count tracking
├─ Payment collection status
├─ Checklist (what vendor needs to provide)
└─ Staff management (assign staff to each event)
```

---

## 📊 VENDOR DASHBOARD LAYOUT

### Desktop (1200px+)
```
┌─────────────────────────────────────────────────┐
│  VENDOR DASHBOARD                               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─ SIDEBAR (320px, sticky) ─┐  ┌─ MAIN CONTENT ─┐
│  │ • Dashboard                │  │ Welcome Card   │
│  │ • My Listings              │  │ ├─ Earnings    │
│  │ • Bookings                 │  │ ├─ Bookings    │
│  │ • Analytics                │  │ ├─ Messages    │
│  │ • Reviews                  │  │ └─ Rating      │
│  │ • Settings                 │  │                │
│  │ • Help                     │  │ KPI Cards (4)  │
│  │                            │  │ ├─ Revenue     │
│  │                            │  │ ├─ Bookings    │
│  │                            │  │ ├─ Avg rating  │
│  │                            │  │ └─ Conversion  │
│  │                            │  │                │
│  │                            │  │ Recent Bookings│
│  │                            │  │ ├─ Table       │
│  │                            │  │ │ ├─ Date      │
│  │                            │  │ │ ├─ Customers │
│  │                            │  │ │ ├─ Amount    │
│  │                            │  │ │ └─ Status    │
│  │                            │  │ └─ View All    │
│  │                            │  │                │
│  │                            │  │ Upcoming Events│
│  │                            │  │ ├─ Calendar    │
│  │                            │  │ └─ Timeline    │
│  │                            │  │                │
│  └────────────────────────────┘  └────────────────┘
│                                                 │
└─────────────────────────────────────────────────┘
```

### Mobile (< 768px)
```
┌──────────────── VENDOR DASHBOARD ─────────────┐
│  ☰ Menu   |   Dashboard   |   Profile   |  ⚙️  │ (header)
├────────────────────────────────────────────────┤
│                                                │
│  Welcome, [Vendor Name]! 👋                   │
│  ├─ Rating: 4.8 ⭐                            │
│  ├─ Earnings this month: ₹2,50,000            │
│  └─ Active bookings: 5                        │
│                                                │
│  ┌─ KPI Card 1 ─────────────┐                │
│  │ Today Bookings: 2        │                │
│  └──────────────────────────┘                │
│                                                │
│  ┌─ KPI Card 2 ─────────────┐                │
│  │ Messages (3 unread)      │                │
│  └──────────────────────────┘                │
│                                                │
│  Recent Bookings                              │
│  ├─ 📅 March 30, 150 guests                  │
│  │   Mr. & Mrs. Sharma                       │
│  │   ₹75,000 | Confirmed ✓                   │
│  └─ [View Details]                           │
│                                                │
│  Upcoming Events                              │
│  ├─ March 22 (Mehandi) - 5 days              │
│  ├─ March 30 (Wedding) - 13 days             │
│  └─ [View All]                               │
│                                                │
│  [Bottom Navigation]                          │
│  Home | Bookings | Chat | Analytics | Profile │
│                                                │
└────────────────────────────────────────────────┘
```

---

## 🎬 KEY SCREEN LAYOUTS (DETAILED)

### Screen 1: Home Page (User)

**Web Layout:**
```
┌────────────────────────────────────────────────────────────────┐
│  Header [Logo] [Search Bar]  [Profile]                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Hero Banner (Full width, 400px height)                       │
│  ├─ Background: Gradient (blue to white)                      │
│  ├─ Title: "Plan Your Perfect Event"                          │
│  ├─ Subheading: "Discover trusted vendors near you"           │
│  ├─ CTA: "Explore Vendors" or "Plan My Event"                 │
│  └─ Imagery: Couple / wedding scene (right side)              │
│                                                                │
│  Featured Vendors (Carousel)                                  │
│  ├─ Heading: "Top-Rated This Week"                            │
│  ├─ Cards (scrollable):                                        │
│  │  ├─ [Vendor Card 1] [Vendor Card 2] [Vendor Card 3]       │
│  │  └─ [See All] button                                       │
│  └─ Show: Image, name, rating, category, price               │
│                                                                │
│  Personalized Recommendations                                 │
│  ├─ Heading: "Recommended for You"                            │
│  ├─ Based on: Your preferences (wedding, ₹50L budget)         │
│  ├─ Cards (grid, 4 columns):                                   │
│  │  ├─ [Card 1] [Card 2] [Card 3] [Card 4]                    │
│  │  └─ [Load More]                                            │
│  └─ Show: Latest matches + AI recommendations                 │
│                                                                │
│  Recent Searches (if any)                                     │
│  ├─ Heading: "Recent Searches"                                │
│  ├─ Tags: [Caterers Delhi] [Photographers] [Decorators]       │
│  └─ Tap to reopen search                                      │
│                                                                │
│  Event Ideas / Inspiration                                    │
│  ├─ Heading: "Get Inspired"                                   │
│  ├─ Articles: "Wedding trends 2026", "Budget tips"            │
│  └─ Tap leads to blog post                                    │
│                                                                │
│  Footer                                                        │
│  ├─ Links: About | Blog | Help | Terms | Privacy             │
│  └─ Contact: support@shadiro.app                              │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  Bottom Nav: Home | Explore | Wishlist | Bookings | Profile   │
└────────────────────────────────────────────────────────────────┘
```

**Mobile Layout:**
```
┌──────────────────────────────────┐
│  [Logo]  [Search]  [Profile]  [🔔] │
├──────────────────────────────────┤
│                                  │
│  [Featured Vendor Carousel]       │ (Full width, auto-scroll)
│  [Card 1] [Card 2] [Card 3] →     │
│                                  │
│  Personalized Recommendations     │
│  [Card 1]                        │ (1 column, scrollable)
│  [Card 2]                        │
│  [Card 3]                        │
│  [Load More]                     │
│                                  │
│  Recent Searches (Tags)           │
│  [Caterers] [Photographers]      │
│  [Decorators] [Makeup Artists]   │
│                                  │
│  Get Inspired (Articles)          │
│  [Article 1]                     │ (Scrollable section)
│  [Article 2]                     │
│                                  │
├──────────────────────────────────┤
│ Home | Explore | ❤️ | 📅 | 👤    │
└──────────────────────────────────┘
```

---

### Screen 2: Vendor Detail Page (Premium Layout)

**Web:**
```
┌────────────────────────────────────────────────────────────────┐
│  [Back] [Search]  [Profile]                                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Hero Image Section (Full width)                              │
│  ├─ Large image carousel (swipeable, 600px height)            │
│  ├─ Image counter (3/8)                                       │
│  ├─ Prev/Next arrows                                          │
│  └─ Floating buttons:                                          │
│      ├─ Heart icon (add to wishlist)                          │
│      ├─ Share icon (WhatsApp, copy link)                      │
│      └─ Report icon                                            │
│                                                                │
│  Vendor Info Header (Sticky on scroll)                        │
│  ├─ Name: "The Grand Palace Caterers"                         │
│  ├─ Category: 🍽️ Caterers & Bakers                           │
│  ├─ Rating: 4.8 ⭐ (328 reviews)                             │
│  ├─ Location: Delhi, India                                    │
│  ├─ Status: ✓ Verified                                        │
│  ├─ Featured: ⭐ Top-Rated                                     │
│  └─ Response time: "Usually responds in 2 hours"              │
│                                                                │
│  Key Info Cards (3 columns)                                   │
│  ├─ Experience: 12 years | 500+ events                        │
│  ├─ Price: From ₹5,00,000 | Per plate ₹800-1500             │
│  └─ Availability: Available March 30, 2026 ✓                  │
│                                                                │
│  Tabs (Sticky): Overview | Packages | Items | Reviews | About │
│                                                                │
│  Tab Content Area                                              │
│  ├─ Overview Tab:                                              │
│  │  ├─ Short description (2-3 lines)                          │
│  │  ├─ Highlights:                                             │
│  │  │  ├─ "North Indian & Continental cuisine"                │
│  │  │  ├─ "Custom menu planning available"                    │
│  │  │  ├─ "Vegetarian & vegan options"                        │
│  │  │  └─ "Experienced service staff"                         │
│  │  ├─ Cancellation Policy section                            │
│  │  └─ Service area map (showing radius)                      │
│  │                                                             │
│  │  ├─ Packages Tab:                                           │
│  │  │  ├─ Card 1: "Essential" - ₹500/plate                   │
│  │  │  │  ├─ What's included (bullet list)                    │
│  │  │  │  └─ [Select Package] button                          │
│  │  │  ├─ Card 2: "Premium" - ₹1000/plate                    │
│  │  │  └─ Card 3: "Luxury" - ₹2000/plate                     │
│  │  │                                                          │
│  │  ├─ Items Tab:                                              │
│  │  │  ├─ Accor dion per item category:                       │
│  │  │  │  ├─ Non-Veg Curries (8 items)                        │
│  │  │  │  │  ├─ Butter Chicken - [Photo] [QTY]               │
│  │  │  │  │  ├─ Lamb Rogan Josh - [Photo] [QTY]              │
│  │  │  │  │  └─ More items...                                 │
│  │  │  │  ├─ Veg Curries (6 items)                            │
│  │  │  │  ├─ Breads (4 items)                                 │
│  │  │  │  ├─ Rice dishes (3 items)                            │
│  │  │  │  ├─ Desserts (5 items)                               │
│  │  │  │  └─ Beverages (2 items)                              │
│  │  │  └─ Total items selected: 15                            │
│  │  │                                                          │
│  │  ├─ Reviews Tab:                                            │
│  │  │  ├─ Rating summary:                                      │
│  │  │  │  ├─ 5⭐: ████████░░ (80%)                            │
│  │  │  │  ├─ 4⭐: ███████░░░ (70%)                            │
│  │  │  │  ├─ 3⭐: ██░░░░░░░░ (20%)                            │
│  │  │  │  ├─ 2⭐: █░░░░░░░░░ (10%)                            │
│  │  │  │  └─ 1⭐: ░░░░░░░░░░ (0%)                             │
│  │  │  ├─ Filter by rating: [All] [5⭐] [4⭐] [3⭐]            │
│  │  │  └─ Reviews list:                                        │
│  │  │     ├─ Review 1                                           │
│  │  │     │  ├─ Sarah Sharma - 5⭐ - "Amazing food & service" │
│  │  │     │  ├─ "Great for wedding. Professional team."       │
│  │  │     │  ├─ Event date: March 12, 2025                    │
│  │  │     │  ├─ [Photo 1] [Photo 2] [Photo 3]                 │
│  │  │     │  └─ Helpful? [❤️ 23] [👎 2] [Report]             │
│  │  │     └─ Review 2, 3, etc.                                 │
│  │  │                                                          │
│  │  └─ About Tab:                                              │
│  │     ├─ Business description (full text)                    │
│  │     ├─ Owner story (optional)                              │
│  │     ├─ Specializations                                     │
│  │     ├─ Experience summary                                  │
│  │     └─ Contact vendor section                              │
│                                                                │
│  Sticky CTA Bar (Bottom, on scroll)                           │
│  ├─ [Request Quote] or [Select Package & Checkout]            │
│  ├─ Price: "From ₹5,00,000" or "₹800/plate"                  │
│  └─ Heart icon for wishlist (toggleable)                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Mobile:**
```
┌──────────────────────────────────┐
│  ← [Search] [❤️] [Share] [...]   │
├──────────────────────────────────┤
│                                  │
│  [Hero Image Carousel]           │
│  (Full width, swipeable)         │
│  [Image 1] → [Image 2]           │
│  (3/8 indicator at bottom)       │
│                                  │
│  Vendor Info Card                │
│  ├─ The Grand Palace Caterers    │
│  ├─ 🍽️ Caterers & Bakers        │
│  ├─ 4.8 ⭐ (328 reviews)        │
│  ├─ ✓ Verified | ⭐ Featured     │
│  ├─ 📍 Delhi, India              │
│  └─ ⏱️ Usually 2 hours response   │
│                                  │
│  Key Info (3 stacked cards)      │
│  ┌─ 12 Years Experience ─────┐  │
│  │ 500+ events completed      │  │
│  └────────────────────────────┘  │
│  ┌─ From ₹5,00,000 total ────┐  │
│  │ ₹800-1500 per plate        │  │
│  └────────────────────────────┘  │
│  ┌─ March 30 Available ✓ ────┐  │
│  │ 100+ slots free            │  │
│  └────────────────────────────┘  │
│                                  │
│  [Tabs: Overview | Packages...]  │
│  (Scrollable horizontally)       │
│                                  │
│  Tab Content (1 column)          │
│  ├─ Highlights                   │
│  │  ├─ North Indian cuisine      │
│  │  ├─ Custom menu planning      │
│  │  └─ Vegetarian options        │
│  │                               │
│  ├─ Packages                     │
│  │  ├─ [Essential - ₹500/plate] │
│  │  ├─ [Premium - ₹1000/plate]  │
│  │  └─ [Luxury - ₹2000/plate]   │
│  │                               │
│  ├─ Items                        │
│  │  ├─ 🔽 Non-Veg Curries (8)   │
│  │  │  ├─ Butter Chicken [QTY]  │
│  │  │  └─ ...                    │
│  │  ├─ 🔽 Veg Curries (6)       │
│  │  └─ ...                       │
│  │                               │
│  ├─ Reviews                      │
│  │  ├─ 4.8 ⭐ (328 reviews)    │
│  │  ├─ 5⭐ 80% | 4⭐ 70% | ...  │
│  │  ├─ Top review:               │
│  │  │  "Amazing food & service"  │
│  │  │  - Sarah Sharma - 5⭐      │
│  │  └─ [See All Reviews]         │
│  └─ ...                          │
│                                  │
├──────────────────────────────────┤
│  [Request Quote] [Select Package] │ (Sticky button, safe area)
│  OR                              │
│  [From ₹5,00,000]                │
└──────────────────────────────────┘
```

---

## 🛒 CHECKOUT FLOW (4 Steps)

**Step 1: Review & Confirm**
```
┌────────────────────────────────┐
│  Checkout: Step 1/4             │
├────────────────────────────────┤
│  Progress Bar: ████░░░░░░       │
│                                │
│  Event Details                 │
│  ├─ Event: Wedding             │
│  ├─ Date: March 30, 2026       │
│  ├─ Time: 6:00 PM              │
│  ├─ Location: Delhi, India     │
│  ├─ Guests: 150                │
│  └─ [Edit] link                │
│                                │
│  Vendor & Package              │
│  ├─ The Grand Palace Caterers  │
│  ├─ Package: Premium Catering  │
│  ├─ ₹1000/plate × 150 guests   │
│  └─ Selected Items:            │
│      ├─ 5 Non-Veg Curries      │
│      ├─ 3 Veg Curries          │
│      ├─ 3 Breads               │
│      ├─ 2 Rice Dishes          │
│      ├─ 2 Desserts             │
│      └─ [View selected items]  │
│                                │
│  Price Breakdown               │
│  ├─ Service charge: ₹1,50,000  │
│  ├─ Taxes (GST): ₹27,000       │
│  ├─ Shadiro fee: ₹5,000        │
│  └─ TOTAL: ₹1,82,000           │
│                                │
│  Special Requests (Shown)      │
│  "No onions, Jain meals needed"│
│                                │
│  [Continue to Payment] →        │
│                                │
└────────────────────────────────┘
```

**Step 2: Payment Method**
```
┌────────────────────────────────┐
│  Checkout: Step 2/4             │
├────────────────────────────────┤
│  Progress Bar: ████████░░       │
│                                │
│  Amount Due: ₹1,82,000          │
│                                │
│  Payment Method                │
│  ○ Credit/Debit Card           │
│    ├─ Card number              │
│    ├─ Expiry & CVV             │
│    └─ Cardholder name          │
│  ○ UPI                         │
│    └─ UPI ID input             │
│  ○ Wallet / Apple Pay          │
│  ○ Net Banking                 │
│                                │
│  Promo Code (Optional)         │
│  [Enter code] → [Apply]        │
│  You could save ₹5,000!        │
│                                │
│  Secure Badge                  │
│  "🔒 Secured by [Provider]"    │
│                                │
│  [Continue to Summary] →        │
│                                │
└────────────────────────────────┘
```

**Step 3: Booking Summary**
```
┌────────────────────────────────┐
│  Checkout: Step 3/4             │
├────────────────────────────────┤
│  Progress Bar: ████████████░░   │
│                                │
│  ✓ Everything Look's Good?     │
│                                │
│  Vendor                        │
│  ├─ [Logo] The Grand Palace   │
│  ├─ Rating: 4.8 ⭐            │
│  ├─ Response: 100% (2 hrs avg) │
│  └─ Verified ✓                 │
│                                │
│  Event Details                 │
│  ├─ March 30, 2026 | 6:00 PM  │
│  ├─ 150 guests | Delhi         │
│  └─ Package: Premium Catering  │
│                                │
│  Total: ₹1,82,000              │
│  ├─ Service: ₹1,50,000         │
│  ├─ Taxes: ₹27,000             │
│  └─ Shadiro fee: ₹5,000        │
│                                │
│  Cancellation Policy           │
│  "Full refund if cancelled     │
│   15 days before event"        │
│  [Read Full Policy]            │
│                                │
│  Protection                    │
│  "✓ Booking protected with    │
│   Shadiro Shield. Vendor     │
│   cancellation = full refund   │
│   or replacement vendor"       │
│                                │
│  Confirm Order                 │
│  ☐ I agree to Terms & Cond.   │
│  ☐ I agree to Cancellation    │
│                                │
│  [Confirm & Pay] ₹1,82,000 →   │
│  [Continue Shopping]            │
│                                │
└────────────────────────────────┘
```

**Step 4: Confirmation**
```
┌────────────────────────────────┐
│  ✓ Booking Confirmed!           │
├────────────────────────────────┤
│                                │
│  Green checkmark + confetti   │
│  animation                     │
│                                │
│  Booking Details               │
│  ├─ Booking ID: SH-2026-5748  │
│  ├─ Vendor: The Grand Palace  │
│  ├─ Date: March 30, 2026      │
│  ├─ Amount: ₹1,82,000         │
│  └─ Status: Confirmed ✓       │
│                                │
│  Next Steps                    │
│  ├─ [📧 Download Invoice]     │
│  ├─ [💬 Chat with Vendor]     │
│  ├─ [📅 Add to Calendar]      │
│  └─ [👥 Share with Family]    │
│                                │
│  Vendor Contact               │
│  ├─ Phone: +91 98765 43210    │
│  ├─ Email: vendor@palace.com  │
│  └─ WhatsApp +91 98765...     │
│                                │
│  Helpful Links                │
│  ├─ View Booking              │
│  ├─ Track Payment             │
│  ├─ Event Timeline            │
│  └─ Contact Support           │
│                                │
│  [Continue Shopping]           │
│  or                            │
│  [Go to Dashboard]             │
│                                │
└────────────────────────────────┘
```

---

## 📧 TRUST SIGNALS & TRANSPARENCY

### "Shadiro Shield" Protection Message
```
Displayed on:
1. Vendor detail page (reassurance)
2. Checkout summary (trust)
3. Post-booking dashboard (confidence)

Message:
"🛡️ Booking Protected with Shadiro Shield
 ✓ Vendor cancellation = Full refund or replacement vendor
 ✓ If vendor doesn't respond within 24 hours, we help
 ✓ Transparent pricing - No hidden charges
 ✓ Secured payment - Your money is safe"
```

### Clear Cancellation Flow
```
If vendor cancels:
1. Notification badge (red, urgent)
2. Modal: "Vendor [name] cancelled - here's what we do"
3. 2 options:
   ├─ Accept replacement vendor (4-5 suggestions shown)
   └─ Request full refund (processed in 1-3 days)
4. Trust message: "Shadiro covers any price difference"
5. Next steps card (prominent)
```

---

**UI Flows Document Status**: 🟢 COMPLETE

**Version**: 1.0  
**Total Screens Designed**: 45+  
**Mobile + Web Layouts**: Both optimized  
**Category Logic**: 4 detailed examples  
**Next Step**: Create component library in Figma/Storybook
