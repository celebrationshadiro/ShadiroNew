# 🔧 Shadiro Component Architecture
## Reusable Components • Props Spec • Tailwind Integration • Shadcn/UI Customization

---

## 📦 Component Hierarchy

```
Root
├── Layout
│   ├── PageLayout (Main container with header/footer)
│   ├── AuthLayout (Sign in/up pages)
│   ├── DashboardLayout (Sidebar + content)
│   └── BottomTabNav (Mobile navigation)
├── Header Components
│   ├── NavBar (Top navigation)
│   ├── SearchBar (Global search)
│   └── NotificationBell
├── Core UI (Shadcn/UI based)
│   ├── Button (Multiple variants)
│   ├── Input (Text fields with variants)
│   ├── Card (Container component)
│   ├── Modal/Dialog (Overlays)
│   ├── Toast/Sonner (Notifications)
│   ├── Badge (Status indicators)
│   ├── Tabs (Tabbed content)
│   └── Dropdown (Select, sort, filter)
├── Business Components
│   ├── VendorCard (Grid/List display)
│   ├── VendorHeader (Detail page header)
│   ├── PackageCard (Service packages)
│   ├── ItemAccordion (Expandable items)
│   ├── ReviewCard (User reviews)
│   ├── BookingCard (Booking status)
│   ├── BookingTimeline (Visual timeline)
│   ├── ChatMessage (Chat bubble)
│   ├── PriceBreakdown (Cost summary)
│   └── EmergencyBanner (Cancellation notification)
├── Forms
│   ├── AuthForm (Sign up/login)
│   ├── VendorRegistrationForm (Multi-step)
│   ├── BookingForm (Event details)
│   ├── FilterPanel (Advanced filters)
│   ├── ChatInput (Message composer)
│   └── ReviewForm (Submit review)
└── Premium Components
    ├── FeaturedBadge (Gold highlight)
    ├── VerificationBadge (Trust signal)
    ├── RatingStars (Star display)
    ├── AvailabilityCalendar (Date picker)
    ├── PriceRange (Budget slider)
    └── ProgressBar (Checkout steps)
```

---

## 🎨 Base Component Library

### Button Component (Shadcn/UI)

```tsx
// File: src/components/ui/Button.tsx

type ButtonVariant = 
  | 'primary'      // Main CTA, blue background
  | 'secondary'    // Less important, border only
  | 'text'         // No background
  | 'premium'      // Gold, for featured vendors
  | 'danger'       // Red, delete/cancel actions
  | 'success'      // Green, confirmation

type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps {
  variant?: ButtonVariant          // default: 'primary'
  size?: ButtonSize                 // default: 'md'
  disabled?: boolean
  loading?: boolean                 // Shows spinner, disables click
  icon?: React.ReactNode           // Leading/trailing icon
  iconPosition?: 'left' | 'right'   // default: 'left'
  fullWidth?: boolean              // Stretch to container width
  onClick?: () => void | Promise<void>
  children: React.ReactNode
}

// Usage Examples:
<Button variant="primary" size="lg">Book Now</Button>
<Button variant="secondary" icon={<Heart />}>Add to Wishlist</Button>
<Button variant="premium" fullWidth>Featured Vendor</Button>
<Button variant="danger" size="sm">Cancel Booking</Button>
<Button loading>Processing...</Button>

// Styling (Tailwind)
primary:     bg-blue-700 hover:bg-blue-800 text-white rounded-lg shadow-md
secondary:   border-2 border-blue-700 text-blue-700 hover:bg-blue-50
text:        bg-transparent text-blue-700 hover:underline
premium:     bg-gold-500 hover:bg-gold-600 text-charcoal shadow-lg glow
danger:      bg-red-500 hover:bg-red-600 text-white
success:     bg-green-500 hover:bg-green-600 text-white

// Touch target: Always 44px × 44px (mobile-friendly)
// Padding: 12px 24px (medium button)
```

### Input Component (Shadcn/UI)

```tsx
// File: src/components/ui/Input.tsx

type InputType = 
  | 'text'
  | 'email'
  | 'phone'
  | 'date'
  | 'number'
  | 'password'
  | 'search'
  | 'textarea'

interface InputProps {
  type?: InputType                 // default: 'text'
  value: string
  onChange: (value: string) => void
  placeholder?: string
  label?: string                   // Associated label
  helper?: string                  // Helper text below input
  error?: string                   // Error message (red)
  disabled?: boolean
  required?: boolean               // Shows * on label
  icon?: React.ReactNode          // Leading icon (search, phone, etc.)
  maxLength?: number
  multiline?: boolean             // For textarea
  rows?: number                    // Textarea rows, default: 4
}

// Usage Examples:
<Input 
  type="email" 
  label="Email Address"
  placeholder="you@example.com"
  value={email}
  onChange={setEmail}
  error="Invalid email format"
/>

<Input 
  type="phone" 
  label="Phone Number"
  icon={<Phone size={20} />}
  placeholder="+91 98765 43210"
/>

<Input 
  type="textarea"
  label="Special Requests"
  placeholder="Tell us your requirements"
  rows={4}
/>

// Styling (Tailwind)
Default:     bg-gray-50 border-gray-200 text-charcoal
Focused:     border-blue-700 shadow-md ring-1 ring-blue-200
Error:       border-red-500 bg-red-50
Disabled:    bg-gray-100 text-gray-400 cursor-not-allowed

// Height: 44px (touch-friendly)
// Padding: 12px 16px
// Font: Inter Medium 16px
```

### Card Component (Shadcn/UI)

```tsx
// File: src/components/ui/Card.tsx

type CardVariant = 
  | 'default'     // Standard white card
  | 'elevated'    // More shadow on hover
  | 'featured'    // Gold accent border
  | 'status'      // Status-colored (pending, confirmed, etc.)

interface CardProps {
  variant?: CardVariant             // default: 'default'
  clickable?: boolean              // Shows hover effect + cursor
  selected?: boolean               // Blue border + background
  onClick?: () => void
  children: React.ReactNode
}

// Usage Examples:
<Card>
  <Card.Header>
    <Card.Title>Vendor Name</Card.Title>
  </Card.Header>
  <Card.Body>
    <p>Card content here</p>
  </Card.Body>
  <Card.Footer>
    <Button>Action</Button>
  </Card.Footer>
</Card>

<Card variant="featured" clickable>
  {/* Featured vendor card */}
</Card>

<Card variant="status" status="confirmed">
  {/* Booking confirmed card */}
</Card>

// Styling (Tailwind)
default:     bg-white rounded-xl shadow-sm border border-gray-100
elevated:    bg-white rounded-xl shadow-md hover:shadow-lg border-none
featured:    bg-white rounded-xl border-t-4 border-gold-500 shadow-lg
status:      bg-[status-color]-50 border-l-4 border-[status-color]-500

// Padding: 20px
// Border radius: 12px
// Transition: All 200ms ease
```

### Badge Component

```tsx
// File: src/components/Badge.tsx

type BadgeVariant = 
  | 'verified'     // Green checkmark
  | 'featured'     // Gold star
  | 'pending'      // Amber pill
  | 'confirmed'    // Green pill
  | 'cancelled'    // Red pill
  | 'category'     // Gray tag

interface BadgeProps {
  variant: BadgeVariant
  label: string
  icon?: React.ReactNode          // Override default icon
  size?: 'sm' | 'md'              // default: 'md'
}

// Usage Examples:
<Badge variant="verified" label="Verified" />
<Badge variant="featured" label="Top-Rated" />
<Badge variant="confirmed" label="Confirmed" />
<Badge variant="category" label="Caterers" size="sm" />

// Styling & Icons:
verified:    ✓ Green bg, "Verified by Shadiro"
featured:    ⭐ Gold bg, "Featured"
pending:     ⏱️ Amber bg, "Pending Response"
confirmed:   ✓ Green bg, "Confirmed"
cancelled:   ✗ Red bg, "Cancelled"
category:    Gray bg, lowercase text

// Sizes:
sm:          h-6 text-xs px-2
md:          h-8 text-sm px-3
```

### Rating Stars Component

```tsx
// File: src/components/RatingStars.tsx

interface RatingStarsProps {
  rating: number                   // 0-5 (accepts decimals like 4.8)
  count?: number                   // Review count (e.g., "328 reviews")
  size?: 'sm' | 'md' | 'lg'       // default: 'md'
  interactive?: boolean            // Allow user selection (for reviews)
  onRatingChange?: (rating: number) => void
}

// Usage Examples:
<RatingStars rating={4.8} count={328} />           // Display only
<RatingStars rating={0} size="lg" interactive />   // For rating form

// Styling:
Star fill:     Gold (#D4AF37)
Star empty:    Gray (#CBD5E0)
Sizes:
  sm:         16px star
  md:         24px star (default)
  lg:         32px star
Interactive hover: Scale 1.1x, slightly brighter
```

### Verification Badge Component

```tsx
// File: src/components/VerificationBadge.tsx

interface VerificationBadgeProps {
  status: 'verified' | 'pending' | 'not_verified'
  size?: 'sm' | 'md'              // default: 'md'
  position?: 'absolute' | 'inline' // default: 'absolute'
}

// Usage Examples:
// Absolute positioning (top-right corner of vendor card)
<div className="relative">
  <img src={vendor.image} />
  <VerificationBadge status="verified" position="absolute" />
</div>

// Inline (in vendor header)
<H3>{vendor.name}</H3>
<VerificationBadge status="verified" position="inline" />

// Styling:
verified:      ✓ Green circle, white checkmark
pending:       ⏳ Gray circle, loading spinner
not_verified:  Gray circle, question mark

Sizes:
  sm:         24px × 24px
  md:         32px × 32px (default)
```

---

## 🎯 Business-Specific Components

### VendorCard Component

```tsx
// File: src/components/VendorCard.tsx

interface VendorCardProps {
  vendor: {
    id: string
    name: string
    category: string
    image: string
    rating: number
    reviewCount: number
    verified: boolean
    featured: boolean
    location: string
    priceRange: { min: number; max: number }
    distance?: number              // In km
  }
  layout?: 'grid' | 'list'         // default: 'grid'
  onCompare?: (vendorId: string) => void
  onBookmark?: (vendorId: string) => void
  isCompared?: boolean             // Checkbox state
  isBookmarked?: boolean           // Heart state
  onClick?: () => void
}

// Grid Layout (Default for listing)
┌─────────────────────────┐
│  [Image]                │
│  ✓ Verified ⭐ Featured│
├─────────────────────────┤
│  Name                   │
│  Category • Location    │
│  4.8 ⭐ (328 reviews)   │
│  From ₹5,000             │
├─────────────────────────┤
│ [❤️] [Compare] [>]      │
└─────────────────────────┘

// List Layout (Horizontal)
┌─────────────────────────────────────────┐
│ [Image] Name                            │
│         Category • Location             │
│         4.8 ⭐ (328) | From ₹5,000     │
│         ✓ Verified | ⭐ Featured        │
│                      [❤️] [Compare] [>] │
└─────────────────────────────────────────┘

// Usage:
<VendorCard 
  vendor={vendorData}
  onCompare={handleCompare}
  isCompared={selectedVendors.includes(vendor.id)}
/>

// Mobile-responsive:
Grid: 2 columns on mobile, 4 on desktop
List: Full-width responsive
```

### VendorHeader Component

```tsx
// File: src/components/VendorHeader.tsx

interface VendorHeaderProps {
  vendor: {
    name: string
    category: string
    location: string
    rating: number
    reviewCount: number
    verified: boolean
    featured: boolean
    responseTime: string        // "Usually 2 hours"
    imageGallery: string[]
  }
  sticky?: boolean             // Becomes sticky on scroll
  onShare?: () => void
  onWishlist?: () => void
}

// Layout:
[Background Image Carousel]      (Full width, 400px height on web)
  ├─ Image 1/8
  ├─ Prev/Next arrows (hover)
  └─ Share & Wishlist buttons (floating)

[Vendor Info Card] (Sticky on scroll down)
  ├─ Name: "The Grand Palace"
  ├─ Category • Location • Rating
  ├─ ✓ Verified | ⭐ Featured
  ├─ Response time badge
  └─ Key stats (3 cards): Experience | Price | Availability

// Sticky positioning:
On desktop: Position absolute, below hero image
On mobile:  Becomes sticky header on scroll
Transition: Smooth slide-in animation
```

### PackageCard Component

```tsx
// File: src/components/PackageCard.tsx

interface PackageCardProps {
  package: {
    id: string
    name: string                   // 'Essential', 'Premium', 'Luxury'
    price: number
    priceUnit: 'flat' | 'per_plate' | 'per_hour'
    description: string
    includedItems: string[]
    addOns?: string[]
    recommended?: boolean
  }
  onSelect?: () => void
  selected?: boolean
  currency?: string              // default: '₹'
}

// Layout:
┌──────────────────────────┐
│ Package Name             │
│ RECOMMENDED (if true)    │
├──────────────────────────┤
│ Price: ₹1,000/plate      │
│                          │
│ Includes:                │
│ • Item 1                 │
│ • Item 2                 │
│ • Item 3                 │
├──────────────────────────┤
│ Add-ons available        │
├──────────────────────────┤
│ [Select This Package] ▶  │
└──────────────────────────┘

// Recommended visual:
Recommended package: Gold border, slight lift (shadow)
Selected package: Blue border, checkmark icon
```

### ItemAccordion Component

```tsx
// File: src/components/ItemAccordion.tsx

interface ItemAccordionProps {
  title: string               // 'Non-Veg Curries', 'Decorations'
  items: {
    id: string
    name: string
    photo?: string
    price?: number
    quantity?: number
    onQuantityChange?: (qty: number) => void
  }[]
  expanded?: boolean
  onToggle?: () => void
  itemLayout?: 'grid' | 'list'
}

// Layout (Expanded):
┌─────────────────────────┐
│ ▼ Non-Veg Curries (8)   │ (Header is clickable)
├─────────────────────────┤
│ [Item 1 Photo] Name       │
│ [QTY selector] ← 1 →      │
│                          │
│ [Item 2 Photo] Name       │
│ [QTY selector] ← 3 →      │
│ ...                      │
└─────────────────────────┘

// Quantity selector:
[−] 0 [+] (stepper buttons)
Tap + adds item, − removes
Can't go below 0, max 50 per item

// Grid layout: 2-3 items per row
// List layout: Full width items
```

### ReviewCard Component

```tsx
// File: src/components/ReviewCard.tsx

interface ReviewCardProps {
  review: {
    id: string
    author: string
    rating: number              // 1-5 stars
    date: Date
    title: string
    body: string
    photos?: string[]
    helpful: number
    notHelpful: number
    vendorReply?: {
      text: string
      date: Date
    }
  }
  onHelpful?: (helpful: boolean) => void
  onReport?: () => void
}

// Layout:
┌─────────────────────────────────┐
│ Sarah Sharma        5⭐         │
│ "Amazing food & service"        │
│ 2 weeks ago                     │
│                                │
│ "Great experience! Professional│
│  team, on-time delivery, food  │
│  was delicious. Highly         │
│  recommended for weddings."    │
│                                │
│ [Photo 1] [Photo 2] [Photo 3]  │
│                                │
│ Helpful? [👍 23] [👎 2]        │
│ [Report inappropriate]         │
│                                │
│ Vendor Reply (if exists):       │
│ ┌                             ┐
│ │ "Thank you Sarah! We        │
│ │  appreciate your feedback." │
│ │ 1 week ago                  │
│ └                             ┘
└─────────────────────────────────┘

// Helpful/Not helpful tracking:
User can toggle helpful or not helpful
Count updates in real-time
```

### BookingCard Component

```tsx
// File: src/components/BookingCard.tsx

interface BookingCardProps {
  booking: {
    id: string
    vendor: {
      id: string
      name: string
      image: string
      category: string
    }
    eventDate: Date
    guestCount: number
    location: string
    amount: number
    status: 'pending' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled'
    cancellationReason?: string    // If cancelled
  }
  onClick?: () => void
  layout?: 'card' | 'compact'
}

// Card Layout:
┌────────────────────────────────┐
│ [Vendor Image] Vendor Name     │
│ 🍽️ Caterers • Delhi           │
├────────────────────────────────┤
│ 📅 March 30, 2026 | 6:00 PM   │
│ 👥 150 guests | Delhi          │
│ 💰 ₹1,82,000                   │
├────────────────────────────────┤
│ Status: Green "Confirmed ✓"    │
│ Countdown: 45 days until event │
├────────────────────────────────┤
│ [Chat] [Details] [Invoice]     │
└────────────────────────────────┘

// Compact Layout (Dashboard list):
Vendor Name | March 30 | 150 guests | ₹1,82,000 | Confirmed ✓ | [>]

// Status colors:
pending:     Amber background
confirmed:   Green background
cancelled:   Red background (with reason tooltip)
```

### BookingTimeline Component

```tsx
// File: src/components/BookingTimeline.tsx

interface BookingTimelineProps {
  eventDate: Date
  phases?: {
    name: string
    icon: React.ReactNode
    daysFromEvent: number
    tasks: {
      name: string
      completed: boolean
    }[]
  }[]
}

// Layout:
[Planning]
  ├─ 🎨 Phase name & icon
  ├─ Current badge (if active)
  ├─ ▼ EXPAND
  │  ├─ ☑ Research vendors
  │  ├─ ☐ Get quotes
  │  ├─ ☐ Compare options
  │  └─ ☐ Book confirmed vendors
  ├─ Progress: 1/4 (25%)
  └─ Progress bar [████░░░░░░]

[Vendor Selection]
  ├─ 📸 (upcoming, grayed out)
  └─ ...

[Logistics]
[Final Prep]
[Event Day]

// Phase detection:
Dynamic calculation based on event date
Shows badge on current phase
Auto-expands current phase
```

### ChatMessage Component

```tsx
// File: src/components/ChatMessage.tsx

interface ChatMessageProps {
  message: {
    id: string
    sender: 'user' | 'vendor'
    text: string
    timestamp: Date
    status?: 'sent' | 'delivered' | 'read'  // For user messages
    isQuote?: boolean                        // Inline quote display
    quote?: {
      vendorName: string
      amount: number
      items: string[]
    }
  }
  showAvatar?: boolean
}

// Layout (User Message):
                          ┌─────────────┐
                          │ "Hello, can │
                          │ you do      │
                          │ gluten      │
                          │ free items?"│
                          │ 2:30 PM  ✓✓ │
                          └─────────────┘

// Layout (Vendor Message):
┌──────────────────────────┐
│ 👤 Vendor Name           │
│ "Sure! We have options"  │
│ 2:32 PM (Delivered)      │
├──────────────────────────┤
│ Quote: Essential Package │
│ ₹500/plate × 150 guests  │
│ [View Full Quote]        │
│ [Accept] [Decline]       │
└──────────────────────────┘

// Styling:
User:       Blue bubble, right-aligned
Vendor:     Gray bubble, left-aligned
Quote:      Separate container with quote styling
```

### PriceBreakdown Component

```tsx
// File: src/components/PriceBreakdown.tsx

interface PriceBreakdownProps {
  breakdown: {
    serviceCharge: number
    tax: number
    platformFee?: number
    discount?: number
    roundingAdjustment?: number
  }
  total: number
  currency?: string              // default: '₹'
  expanded?: boolean
  onToggle?: () => void
}

// Layout (Compact):
Total: ₹1,82,000
[Show breakdown ▼]

// Layout (Expanded):
Service charge        ₹1,50,000
Tax (12% GST)        +₹18,000
Shadiro fee          +₹5,000
─────────────────────────────
Total                ₹1,73,000

If discount:
Discount             -₹5,000
─────────────────────────────
Final Total          ₹1,68,000

// Styling:
Left column (labels):    Right column (amounts):
Regular weight           Bold weight
Gray text (secondary)    Blue text (primary)
```

### EmergencyBanner Component

```tsx
// File: src/components/EmergencyBanner.tsx

interface EmergencyBannerProps {
  emergency: {
    bookingId: string
    vendorName: string
    cancelReason: string
    suggestedReplacements: number
  }
  onViewReplacements?: () => void
  onRequestRefund?: () => void
  onDismiss?: () => void
}

// Layout:
┌─────────────────────────────────┐
│ ⚠️ URGENT: Vendor Cancelled     │
├─────────────────────────────────┤
│ [Vendor Name] cancelled due to: │
│ "[Cancellation Reason]"         │
│                                │
│ ✓ Good news: 4 alternatives    │
│ found for your date            │
│                                │
│ [View Replacements ▶]          │
│ [Request Full Refund]          │
│ [X Dismiss]                    │
└─────────────────────────────────┘

// Styling:
Background:  Red-50 (#FEE2E2)
Border:      2px red (#EF4444)
Title:       Bold, large
Action CTAs: Primary & secondary buttons
Animation:   Slide-down from top, smooth
```

---

## 🎨 Advanced Component Patterns

### Sticky CTA Pattern

```tsx
// File: src/components/StickyCTA.tsx

interface StickyCtaProps {
  label: string                   // 'Book Now', 'Request Quote'
  price?: string | number
  onClick: () => void
  loading?: boolean
  disabled?: boolean
  variant?: 'primary' | 'premium'
}

// Behavior:
1. Position: Fixed at bottom of viewport (mobile) / Right sidebar (web)
2. Visibility: Always visible while scrolling
3. Safe area: Respects bottom tab navigation (80px margin on mobile)
4. Animation: Slides up from bottom on page load
5. On click: Smooth scroll to modal / checkout

// Mobile positioning:
[Page content scrolls]
─────────────────────────
║ [REQUEST QUOTE] ₹50,000 ║  (Always visible)
║  (Safe area padding)    ║
└─────────────────────────
│ Bottom tab nav (80px)   │
└─────────────────────────
```

### Filter Panel Pattern

```tsx
// File: src/components/FilterPanel.tsx

interface FilterPanelProps {
  filters: {
    category?: string[]
    priceRange?: [number, number]
    rating?: number
    verified?: boolean
    distance?: number
    availability?: Date
  }
  onFilterChange: (filters: typeof filtersType) => void
}

// Mobile: Bottom sheet
// Desktop: Sidebar collapse/expand

// Filter sections:
1. Category (checkbox group)
2. Price range (slider, dual-handle)
3. Minimum rating (select 3+, 4+, 4.5+, 5)
4. Verification status (toggle)
5. Distance (slider, "Near me" preset)
6. Availability (date picker)

// CTA at bottom: [Apply Filters] [Reset]
// Results update: Realtime or on button tap
```

### Tabs Component (Shadcn/UI + Custom)

```tsx
// File: src/components/Tabs.tsx

interface TabsProps {
  tabs: {
    id: string
    label: string
    content: React.ReactNode
    badge?: number              // For notification count
  }[]
  sticky?: boolean            // Sticky on scroll
  variant?: 'default' | 'underline'
  onChange?: (tabId: string) => void
}

// Usage (Vendor Detail):
<Tabs
  tabs={[
    { id: 'overview', label: 'Overview', content: <Overview /> },
    { id: 'packages', label: 'Packages', content: <Packages /> },
    { id: 'items', label: 'Items', content: <Items /> },
    { id: 'reviews', label: 'Reviews', badge: 328, content: <Reviews /> },
    { id: 'about', label: 'About', content: <About /> }
  ]}
  sticky
/>

// Styling:
Underline variant: Border-bottom active state
Default variant:   Background color change
Animation:         Smooth scroll-to-tab on mobile
```

---

## 📱 Responsive Patterns

### Grid Component (Custom Wrapper)

```tsx
// File: src/components/Grid.tsx

interface GridProps {
  columns?: {
    mobile: number              // < 768px
    tablet: number              // 768px - 1200px
    desktop: number             // > 1200px
  }
  gap?: 'sm' | 'md' | 'lg'      // 8px, 16px, 24px
  children: React.ReactNode
}

// Usage:
<Grid columns={{ mobile: 1, tablet: 2, desktop: 4 }} gap="md">
  {vendors.map(vendor => <VendorCard vendor={vendor} />)}
</Grid>

// Tailwind Grid Classes:
mobile:   grid-cols-1
tablet:   md:grid-cols-2
desktop:  lg:grid-cols-4
```

### Container Component

```tsx
// File: src/components/Container.tsx

interface ContainerProps {
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  padding?: 'xs' | 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

// Max widths:
sm:    512px
md:    768px
lg:    1024px
xl:    1200px
full:  100%

// Usage:
<Container maxWidth="lg" padding="md">
  {children}
</Container>
```

---

## 🔗 Component Integration Guide

### Example Page: Vendor Listing

```tsx
// File: src/pages/VendorListing.tsx

export default function VendorListingPage() {
  const [filters, setFilters] = useState({})
  const [vendors, setVendors] = useState([])
  const [selectedVendors, setSelectedVendors] = useState([])
  
  return (
    <PageLayout>
      <Container maxWidth="lg">
        {/* Header */}
        <h1>Caterers in Delhi</h1>
        <p>Found 28 matching vendors</p>
        
        {/* Layout: Sidebar + Content */}
        <div className="flex gap-lg md:gap-xl">
          {/* Sidebar */}
          <aside className="w-80 hidden md:block">
            <FilterPanel 
              filters={filters}
              onFilterChange={setFilters}
            />
          </aside>
          
          {/* Mobile Filter Button */}
          <button className="md:hidden">
            Filter Results
          </button>
          
          {/* Main Content */}
          <main className="flex-1">
            <Grid 
              columns={{ mobile: 1, tablet: 2, desktop: 4 }}
              gap="md"
            >
              {vendors.map(vendor => (
                <VendorCard
                  key={vendor.id}
                  vendor={vendor}
                  onCompare={(id) => handleCompare(id)}
                  isCompared={selectedVendors.includes(vendor.id)}
                />
              ))}
            </Grid>
            
            {/* Sticky Compare button */}
            {selectedVendors.length > 0 && (
              <button className="fixed bottom-20 right-4 md:right-8">
                Compare {selectedVendors.length}
              </button>
            )}
          </main>
        </div>
      </Container>
    </PageLayout>
  )
}
```

### Example Page: Vendor Detail

```tsx
// File: src/pages/VendorDetail.tsx

export default function VendorDetailPage() {
  const [activeTab, setActiveTab] = useState('overview')
  
  return (
    <PageLayout>
      {/* Hero Section */}
      <VendorHeader vendor={vendor} sticky />
      
      {/* Main Content */}
      <Container maxWidth="lg" padding="lg">
        <Tabs
          tabs={[
            { id: 'overview', label: 'Overview', ... },
            { id: 'packages', label: 'Packages', ... },
            { id: 'items', label: 'Items', ... },
            { id: 'reviews', label: 'Reviews', ... },
            { id: 'about', label: 'About', ... }
          ]}
          sticky
          onChange={setActiveTab}
        />
      </Container>
      
      {/* Sticky CTA */}
      <StickyCTA 
        label={`Request Quote` | `Select Package`}
        price={vendor.startingPrice}
        onClick={handleCTA}
      />
    </PageLayout>
  )
}
```

---

## 🎨 Tailwind CSS Integration

### Color Tokens (tailwind.config.js)

```javascript
module.exports = {
  theme: {
    colors: {
      // Brand colors
      primary: {
        700: '#2C5285',
        800: '#1A365D',
      },
      gold: {
        500: '#D4AF37',
        600: '#AA8C2C',
      },
      charcoal: '#2D3748',
      
      // Semantic colors
      success: '#48BB78',
      caution: '#ED8936',
      alert: '#F56565',
      
      // Grays
      gray: {
        50:  '#F7FAFC',
        100: '#EDF2F7',
        200: '#E2E8F0',
        // ... standard gray scale
      }
    },
    spacing: {
      'xs': '4px',
      'sm': '8px',
      'md': '16px',
      'lg': '24px',
      'xl': '32px',
    },
    borderRadius: {
      'sm': '6px',
      'md': '12px',
      'lg': '16px',
      'full': '9999px',
    },
    shadow: {
      'sm': '0 2px 8px rgba(0,0,0,0.08)',
      'md': '0 4px 16px rgba(0,0,0,0.12)',
      'lg': '0 8px 32px rgba(0,0,0,0.16)',
      'xl': '0 12px 48px rgba(0,0,0,0.20)',
    }
  }
}
```

### Utility Classes (Custom CSS)

```css
/* src/styles/utilities.css */

/* Shadows */
.shadow-elevation-1  { @apply shadow-sm; }
.shadow-elevation-2  { @apply shadow-md; }
.shadow-elevation-3  { @apply shadow-lg; }
.shadow-elevation-4  { @apply shadow-xl; }

/* Premium effects */
.glow-premium {
  box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
}

/* Touch areas */
.touch-target {
  @apply min-h-11 min-w-11; /* 44px */
}

/* Text truncation */
.truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Animations */
@keyframes slide-up {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0);   opacity: 1; }
}

.animate-slide-up {
  animation: slide-up 300ms ease-out;
}
```

---

## 📋 Component Checklist

### Core UI Components (Shadcn/UI)
- [ ] Button (all 5 variants)
- [ ] Input (text, email, phone, date, textarea)
- [ ] Card (container)
- [ ] Modal/Dialog
- [ ] Toast/Sonner
- [ ] Badge
- [ ] Tabs
- [ ] Dropdown

### Business Components
- [ ] VendorCard (grid/list)
- [ ] VendorHeader
- [ ] PackageCard
- [ ] ItemAccordion
- [ ] ReviewCard
- [ ] BookingCard
- [ ] BookingTimeline
- [ ] ChatMessage
- [ ] PriceBreakdown
- [ ] EmergencyBanner

### Forms & Inputs
- [ ] AuthForm
- [ ] VendorRegistrationForm
- [ ] BookingForm
- [ ] FilterPanel
- [ ] ChatInput
- [ ] ReviewForm

### Layout Components
- [ ] PageLayout
- [ ] AuthLayout
- [ ] DashboardLayout
- [ ] BottomTabNav
- [ ] Container
- [ ] Grid

### Advanced Components
- [ ] StickyCTA
- [ ] AvailabilityCalendar
- [ ] PriceRange (slider)
- [ ] ProgressBar (checkout)
- [ ] RatingStars
- [ ] VerificationBadge

---

## 🚀 Build & Export Strategy

### Component Library Structure
```
src/
├── components/
│   ├── ui/                    (Shadcn/UI base)
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Tabs.tsx
│   │   ├── Modal.tsx
│   │   └── Toast.tsx
│   ├── shared/                (Reusable business components)
│   │   ├── VendorCard.tsx
│   │   ├── PackageCard.tsx
│   │   ├── ReviewCard.tsx
│   │   ├── BookingCard.tsx
│   │   ├── VendorHeader.tsx
│   │   ├── StickyCTA.tsx
│   │   ├── PriceBreakdown.tsx
│   │   └── EmergencyBanner.tsx
│   ├── forms/                 (Form-specific components)
│   │   ├── AuthForm.tsx
│   │   ├── FilterPanel.tsx
│   │   ├── ChatInput.tsx
│   │   └── ReviewForm.tsx
│   ├── layout/                (Layout wrappers)
│   │   ├── PageLayout.tsx
│   │   ├── DashboardLayout.tsx
│   │   └── Container.tsx
│   └── icons/                 (Lucide React icons)
│       ├── index.tsx
│       └── custom/
├── styles/
│   ├── globals.css
│   ├── utilities.css
│   └── animations.css
└── lib/
    └── tailwind-config.ts
```

### Export Pattern (index.ts)
```typescript
// src/components/index.ts
export { Button } from './ui/Button'
export { Input } from './ui/Input'
export { Card } from './ui/Card'
export { VendorCard } from './shared/VendorCard'
export { PackageCard } from './shared/PackageCard'
// ... all exports
```

---

**Component Architecture Status**: 🟢 READY FOR BUILD

**Total Components**: 40+  
**Shadcn/UI Integration**: Complete  
**Tailwind Customization**: Full theme tokens  
**Responsive**: Mobile-first design  
**Accessibility**: WCAG 2.1 AA ready
