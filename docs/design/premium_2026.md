# 🎨 Shadiro Design System 2026
## Premium Event Platform • Trust-First UX • India's Most Elegant Local Marketplace

---

## 📐 Core Design Philosophy

### The Shadiro Principles
1. **Minimal Luxury** — Every pixel earns its place. No visual clutter.
2. **Emotion First** — Wedding/event planning is stressful. We make it calm.
3. **Trust Transparency** — Clear pricing, clear status, clear communication.
4. **Effortless Discovery** — Find what you need in 3 taps max.
5. **Mobile-Native Mindset** — Design mobile first; web is enhanced mobile.

### Design Hierarchy
```
Premium Feel (Luxury)
    ↓
Trust Signals (Verified, Reviews)
    ↓
Emotional Calm (Soft UI, Breathing Room)
    ↓
Action-Ready (Clear CTAs, No Confusion)
```

---

## 🎨 Color Palette

### Primary Brand Colors
```
Primary Blue        #2C5285  (Trust, professionalism, depth)
Accent Gold         #D4AF37  (Premium, luxury, celebration)
Pure White          #FFFFFF  (Space, clarity, elegance)
Soft Charcoal       #2D3748  (Text, hierarchy, warmth)
```

### Semantic Colors
```
Success Green       #48BB78  (Confirmed, verified, available)
Caution Amber       #ED8936  (Pending, review needed)
Alert Red          #F56565  (Cancelled, urgent, error)
Subtle Gray        #EDF2F7  (Disabled, inactive, secondary)
```

### Gradients (Premium)
```
Trust Linear:       #2C5285 → #1A365D  (Dark blue depth)
Gold Shimmer:       #D4AF37 → #AA8C2C  (Luxury feel)
Calm Radial:        #FFFFFF → #F7FAFC  (Soft breathing)
```

### Usage Guidelines
- **Primary Blue**: Main CTAs, navigation, trust badges
- **Accent Gold**: Premium tags, featured vendors, celebration moments
- **White/Gray**: Content areas, breathing room
- **Semantic**: Status only (never for branding)

---

## 🔤 Typography System

### Font Stack
```
Headings:    Playfair Display Bold  (H1-H4)
             (Serif, elegant, wedding-forward)
             
Body:        Inter Medium          (14-16px regular)
             (Clean, readable, modern)
             
Accents:     Inter SemiBold        (Labels, CTAs)
```

### Scale & Usage
```
H1: 48px Playfair Bold   → Page titles ("Find Caterers")
H2: 36px Playfair Bold   → Section headers
H3: 24px Playfair Bold   → Card titles, vendor names
H4: 20px Playfair Bold   → Subheaders
Body: 16px Inter         → Paragraph text
Small: 14px Inter        → Descriptions, metadata
Tiny: 12px Inter Gray    → Timestamps, secondary info
```

### Line Heights
- Headings: 1.2 (tight, elegant)
- Body: 1.6 (readable, spacious)
- Labels: 1.4 (balanced)

---

## 📏 Spacing System

### Base Unit: 8px Grid
```
Micro:      4px   (borders, thin gaps)
XSmall:     8px   (internal padding)
Small:      12px  (component gaps)
Medium:     16px  (card padding, section gaps)
Large:      24px  (major sections)
XLarge:     32px  (page sections)
Jumbo:      48px  (major breaks)
```

### Component Spacing
```
Card Padding:           16-24px
Button Height:          44px (touch-friendly)
Input Height:           44px (touch-friendly)
Bottom Sheet Padding:   20px (safe area)
Sidebar Width:          320px (max)
Max Content Width:      1200px (web)
Mobile Breakpoint:      < 768px
```

---

## 🎭 Shadow & Depth System

### Elevation Levels
```
Level 0 (None):        No shadow
                       Usage: Neutral backgrounds, disabled states

Level 1 (Card):        0 2px 8px rgba(0,0,0,0.08)
                       Usage: Cards, form inputs

Level 2 (Hover):       0 4px 16px rgba(0,0,0,0.12)
                       Usage: Card hover, elevated buttons

Level 3 (Modal):       0 8px 32px rgba(0,0,0,0.16)
                       Usage: Modals, dropdowns, overlays

Level 4 (Premium):     0 12px 48px rgba(0,0,0,0.20)
                       Usage: Featured vendors, sticky CTAs
```

### Border Radius
```
Micro:    2px   (tiny elements, fine details)
Small:    6px   (buttons, inputs, badges)
Medium:   12px  (cards, tags)
Large:    16px  (major containers)
XLarge:   24px  (featured cards)
Full:     9999px (pills, avatars)
```

---

## 🔘 Component Foundation

### Button System
```
Primary Button (Book Now / Request Quote)
├─ Background: #2C5285
├─ Text: White
├─ Height: 44px
├─ Radius: 8px
├─ Icon + Label (leading icon preferred)
├─ Hover: Darker blue (#1A365D) + subtle lift
├─ Active: Pressed state + transition
└─ States: Default, Loading (spinner), Disabled (gray)

Secondary Button (Compare, Add to Wishlist)
├─ Background: Transparent with border
├─ Text: #2C5285
├─ Border: 1px solid #2C5285
├─ Hover: Light blue background
└─ Same states as primary

Text Button (Skip, Learn More)
├─ Background: None
├─ Text: #2C5285 underline
├─ Hover: Gold accent
└─ No padding required

Premium Button (Featured Vendor)
├─ Background: Gold (#D4AF37)
├─ Text: #2D3748
├─ Glow effect on hover
└─ Usage: CTAs for top-rated vendors
```

### Input Fields
```
Text Input / Textarea
├─ Height: 44px (touch-friendly)
├─ Background: #F7FAFC (soft gray)
├─ Border: 1px solid #CBD5E0
├─ Radius: 8px
├─ Padding: 12px 16px
├─ Focus: Blue border (#2C5285) + shadow
├─ Placeholder: Gray (#A0AEC0)
└─ Label: Required indicator (*)

Dropdown / Select
├─ Same styling as input
├─ Icon: Chevron down (right side)
├─ Open: Blue border + dropdown appears
└─ Mobile: Native select on small screens

Date & Time Picker
├─ Calendar popup (modal on mobile)
├─ Current date highlighted in blue
├─ Selected dates: Gold background
├─ Range selection: Blue band between dates
└─ Time: 2-column picker (hours / minutes)

Checkbox & Radio
├─ 24px × 24px (touch-friendly)
├─ Unchecked: Gray border
├─ Checked: Blue background with white checkmark
├─ Radio: Blue filled circle
└─ Labels to the right (no padding needed)
```

### Card Components
```
Standard Card
├─ Background: White
├─ Border: None
├─ Shadow: Level 1 (subtle elevation)
├─ Radius: 12px
├─ Padding: 16px (internal)
├─ Hover: Level 2 shadow + scale(1.02)
└─ Transition: 200ms ease

Vendor Card (Grid Layout)
├─ Image: 1:1 ratio (cropped)
├─ Badge: "Verified" / "Featured" (top-right)
├─ Title: Vendor name (H4)
├─ Meta: Category, city, rating
├─ Action: Floating action button (bottom-right)
└─ On mobile: Full width, 2 columns max

Featured Card (Gold Premium)
├─ All standard card + gold accent border (2px top)
├─ Glow effect: Gold shadow
├─ "Featured" badge prominent
└─ Slightly larger on grid (1.2x scale)

Booking Card (Status Display)
├─ Header: Vendor name + category icon
├─ Middle: Event date, guest count, amount
├─ Bottom: Status badge + action button
├─ Pending: Amber background
├─ Confirmed: Green background
├─ Cancelled: Red background (with reason)
└─ Interactive: Tap to view details
```

### Badge & Tag System
```
Verification Badge
├─ Icon: Checkmark in circle
├─ Color: Green (#48BB78)
├─ Text: "Verified" or just icon
├─ Size: 24px × 24px
└─ Placement: Vendor card top-right

Featured Badge
├─ Icon: Star
├─ Color: Gold (#D4AF37)
├─ Text: "Featured" or "Top-Rated"
└─ Prominent display

Status Badge
├─ Pending: Amber pill (12px height)
├─ Confirmed: Green pill
├─ Cancelled: Red pill
├─ In Progress: Blue pill
└─ Completed: Gray pill

Category Tag
├─ Background: Light gray (#EDF2F7)
├─ Text: Charcoal (#2D3748)
├─ Radius: Full (pill shape)
├─ Size: Compact (12px text)
└─ Multiple tags in row, wrap on mobile
```

---

## 📱 Layout Foundations

### Web Grid System
```
Desktop (> 1200px):
├─ Full width content area
├─ 4-column grid (vendors, products)
├─ Sidebar navigation (left 320px)
└─ Max content: 1200px centered

Tablet (768px - 1200px):
├─ 2-column grid
├─ Collapsible sidebar
└─ Flexible spacing

Mobile (< 768px):
├─ Single column (100% width)
├─ Bottom tab navigation
├─ Full-screen modals
└─ No sidebar (drawer instead)
```

### Mobile UI Patterns
```
Bottom Tab Navigation (5 tabs max)
├─ Home (house icon)
├─ Explore (search icon)
├─ Wishlist (heart icon)
├─ Bookings (calendar icon)
└─ Profile (person icon)

Bottom Sheet (for inputs, filters)
├─ Slides up from bottom
├─ Drag handle at top
├─ 90vh max height
├─ Keyboard-aware
└─ Dismiss by pulling down

Safe Areas
├─ Top: 44px (status bar)
├─ Bottom: 80px (tab bar) + safe area
├─ Buttons: Never below 80px from bottom
└─ Content: 16px margins from edges

Sticky Actions
├─ CTA button (Book Now, Request Quote)
├─ Stays at bottom (above tab bar)
├─ 44px height
├─ Full width with 16px margins
└─ Visible while scrolling
```

---

## ✨ Premium UI Patterns

### Trust Signals (Builds Confidence)
```
Verification Badge
├─ Verified by Shadiro ✓
├─ Profile completion: 89%
├─ Identity verified: Yes
└─ Avg response time: 2 hours

Review Preview
├─ 4.8 ⭐ (328 reviews)
├─ 3 star breakdown chart
├─ "See all reviews" link
└─ Latest 2 reviews shown inline

Featured Tag
├─ "Top-Rated in Delhi"
├─ "Most Booked Caterer"
├─ Gold badge, prominent
└─ Builds premium perception

Transparent Pricing
├─ "No hidden charges" label
├─ All-in price breakdown
├─ What's included / not included
└─ Clear cancellation policy
```

### Emotional Calm Design
```
White Space
├─ Generous padding between sections
├─ Breathing room between cards
├─ Not cramped, not sparse
└─ 24-32px between major sections

Soft Micro-interactions
├─ Fade-in for new content (200ms)
├─ Scale-up for cards on hover (1.02x)
├─ Smooth color transitions (300ms)
├─ Haptic on mobile (subtle feedback)
└─ No jarring animations

Progress Indicators
├─ Linear progress for checkout steps
├─ Circular progress for loading
├─ "Matched with X vendors" progress
└─ Event timeline progress (visual)

Reassurance Messages
├─ "We've matched you with 5 vendors"
├─ "Your quote request sent successfully"
├─ "Vendor usually responds within 2 hours"
├─ "Your booking is protected"
└─ Bottom toast notifications, non-intrusive
```

### Sticky CTA (Conversion Focused)
```
On Vendor Detail Page
├─ "Request Quote" button (sticky, bottom)
├─ OR "Book Now" button (if packages available)
├─ Price visible next to button
├─ Visible while scrolling up/down
├─ Tap to open checkout/chat
└─ Desktop: Right sidebar position, web: bottom

On Listing Page
├─ No sticky CTA (too aggressive)
├─ Card-level action buttons only
└─ Mobile: Tap card to open detail → sticky CTA

On Mobile
├─ 44px button height (thumb-friendly)
├─ Safe area respected (80px from bottom)
├─ Full width with 16px margins
└─ Tap target: 44px min
```

---

## 🎯 Status & State Design

### Booking Status Flow (Visual Feedback)
```
1. Quote Request
   Badge: Amber "Pending Response"
   Message: "Vendor usually responds in 2 hours"
   Action: "View quote details"

2. Quote Received
   Badge: Amber "Quote Received"
   Message: "Review & compare pricing"
   Action: "View quote" / "Request revision" / "Accept quote"

3. Confirmed / Accepted
   Badge: Green "Confirmed"
   Message: "Payment due by [date]"
   Action: "Pay now" / "Chat with vendor"

4. Payment Complete
   Badge: Green "Payment Complete"
   Message: "Event is protected with Shadiro shield"
   Action: "View booking details" / "Chat"

5. In Progress
   Badge: Blue "Event in Progress"
   Message: "Countdown to event"
   Action: "Live chat with vendor"

6. Completed
   Badge: Gray "Completed"
   Message: "Rate & review your experience"
   Action: "Write review"

7. Cancelled
   Badge: Red "Cancelled"
   Message: "Refund processed: ₹X amount"
   Reason: "Vendor cancelled due to emergency"
   Action: "View replacement options" / "Request refund history"
```

### Emergency Cancellation Flow (Trust-First)
```
1. Vendor Cancels (Red Alert)
   ├─ Push notification: "Action needed - vendor cancelled"
   ├─ App badge: Red dot with count
   ├─ Current page: Top banner (red, urgent but calm)
   ├─ Message: "Vendor [name] cancelled due to [reason]"
   └─ CTA: "View alternatives (4 matching vendors found)"

2. Replacement Suggestions
   ├─ Modal/Page: 4-5 vendors matched
   ├─ Each shows: Ratings, price, availability, reviews
   ├─ "Guarantee": "Replacement vendor confirmed within 24 hours"
   ├─ Action: "Accept replacement" or "Request refund"
   └─ Message: "Shadiro covers any price difference"

3. Replacement Accepted
   ├─ Booking updated with new vendor
   ├─ Green success message
   ├─ New vendor intro: "Meet your new vendor [name]"
   ├─ Message: "Vendor confirmed for your event date"
   └─ Action: "Chat with new vendor"

4. Refund Requested
   ├─ Processing message: "Refund processing (1-3 business days)"
   ├─ Amount shown: ₹X to be refunded
   ├─ Trust message: "Shadiro refund protection covers this"
   └─ Timeline: Estimated delivery date

5. Post-Cancellation
   ├─ Event timeline still visible
   ├─ Help section: Resources for finding replacement
   ├─ Message: "We're here to help - chat with our team"
   └─ CTA: "Browse similar vendors"
```

---

## 🎬 Transition & Animation Guidelines

### Page Transitions
- **Route Change**: Fade-in (200ms) + subtle slide-up (50px)
- **Modal Open**: Fade background + scale-up from center
- **Bottom Sheet**: Slide-up from bottom (300ms) with easing

### Micro-interactions
- **Button Click**: Scale feedback (98% → 100%) + color transition
- **Card Hover**: Shadow elevation + scale (1.02x)
- **Input Focus**: Border color change (200ms) + glow effect
- **Loading State**: Pulse or spinner (2s infinite)

### Performance Guidelines
- **All animations**: < 300ms for responsiveness
- **page load**: CSS animations only, no JS unless needed
- **Mobile**: Reduced motion preference respected (prefers-reduced-motion)

---

## 🌙 Dark Mode (Future Consideration)

### Planned for Q2 2026
```
Background:          #1A202C (dark charcoal)
Text Primary:        #FFFFFF
Text Secondary:      #CBD5E0
Card Background:     #2D3748
Accent Blue:         #63B3ED (lighter for contrast)
Accent Gold:         #F6AD55 (warmer on dark)

Implementation:
├─ CSS variables: --color-bg, --color-text, etc.
├─ Auto-detect: prefers-color-scheme
├─ Toggle in Settings
└─ Persist in localStorage
```

---

## 📊 Future AI/Automation Hooks (2027-2030)

### Design Points for AI Integration (Non-Intrusive)
```
Recommendation Engine
├─ Soft suggestion banner: "You might like..."
├─ Not mandatory, easily dismissed
├─ Based on: History, preferences, budget
└─ Floating badge (when scrolling): "X new matches"

Smart Search
├─ As-you-type suggestions
├─ Category predictions ("Looking for: Caterers?")
├─ Budget estimation ("Budget: ₹3-5L suggested")
└─ Filter auto-fill based on event type

Vendor Availability AI
├─ "This vendor available for your date ✓"
├─ "Slightly out of budget, but highly rated"
├─ "Vendor can help with setup, menu planning, etc."
└─ Async notification when vendor responds

Booking Summary AI
├─ Auto-generated summary: "Wedding for 150 guests, ₹50L budget"
├─ Timeline suggestion: "Book vendors 3-6 months in advance"
├─ Checklist: Auto-created timeline based on event date
└─ Smart reminders: "Time to finalize catering"

Price Intelligence
├─ "Average price for this service: ₹5,000"
├─ "This vendor is 10% below market"
├─ "You saved ₹15,000 using Shadiro"
└─ Transparent, trust-building data
```

---

## ♿ Accessibility (WCAG 2.1 AA)

### Core Standards
- **Color Contrast**: 4.5:1 for text, 3:1 for graphics
- **Focus States**: Visible blue outline (2px) on all interactive elements
- **Alt Text**: All images have descriptive alt
- **Keyboard Nav**: All features keyboard accessible
- **Screen Reader**: Proper ARIA labels, semantic HTML

### Mobile Accessibility
- **Touch Targets**: 44px × 44px minimum
- **Text Size**: Min 14px (user scalable)
- **Haptic**: Subtle feedback on actions
- **Color**: Never rely on color alone for meaning

---

## 📐 Comparison to Industry Standards

| Feature | Shadiro | Airbnb | Shaadi.com |
|---------|---------|--------|-----------|
| Trust Signals | ✅ Prominent | ✅ Prominent | ✅ Prominent |
| Pricing Clarity | ✅ 100% transparent | ✅ Mostly clear | ⚠️ Hidden charges |
| Mobile UX | ✅ Native-first | ✅ Flawless | ⚠️ Needs work |
| Emotional Design | ✅ Calm & minimal | ✅ Inspiring | ⚠️ Corporate |
| Category Logic | ✅ Dynamic forms | ⚠️ One-size-fits-all | ⚠️ Limited |
| Emergency UX | ✅ Transparent | ✅ Good | ❌ Poor |
| AI Personalization | ✅ Planned | ✅ Advanced | ⚠️ Basic |

---

## 🚀 Implementation Roadmap

### Phase 1 (Weeks 1-4): Foundation
- [ ] Design system tokens (colors, typography, spacing)
- [ ] Shadcn/UI component customization (buttons, inputs, cards)
- [ ] Tailwind color palette integration
- [ ] Create component library in Figma / Storybook

### Phase 2 (Weeks 5-8): Core Flows
- [ ] Landing page design & build
- [ ] Auth flow (sign up, login, password recovery)
- [ ] Vendor listing with filters
- [ ] Vendor detail page with packages

### Phase 3 (Weeks 9-12): Transactions
- [ ] Chat interface (WhatsApp-style)
- [ ] Booking checkout flow (4 steps)
- [ ] Payment integration UI
- [ ] Booking confirmation & timeline

### Phase 4 (Weeks 13-16): Dashboards
- [ ] User dashboard (bookings, timeline, saved)
- [ ] Vendor dashboard (analytics, active bookings)
- [ ] Admin control panel (moderation, reports)

### Phase 5 (Weeks 17-20): Polish & Mobile
- [ ] Mobile app (React Native) with same design
- [ ] Dark mode implementation
- [ ] Performance optimization
- [ ] QA & user testing

### Phase 6 (Weeks 21+): AI & Future
- [ ] Recommendation engine UI
- [ ] Smart search suggestions
- [ ] AI-generated summaries
- [ ] Automation workflows

---

## 📋 Design Deliverables Checklist

- [ ] Master Figma file (all screens)
- [ ] Component library (Shadcn + custom)
- [ ] CSS tokens (colors, spacing, shadows)
- [ ] Icon system (all 50+ icons)
- [ ] Animation specs (Framer Motion patterns)
- [ ] Mobile mockups (iPhone 15, Android)
- [ ] Accessibility audit (WCAG AA)
- [ ] Responsive breakpoints guide
- [ ] Dark mode color definitions
- [ ] Interaction patterns (micro-interactions)
- [ ] Performance benchmarks (Lighthouse)
- [ ] Design system documentation (living guide)

---

**Design System Status**: 🟢 READY FOR IMPLEMENTATION

**Version**: 1.0 (February 2026)  
**Next Review**: Q4 2026 (post-launch updates)  
**Inspiration**: Airbnb's trust, Apple's minimalism, Shaadi's elegance
