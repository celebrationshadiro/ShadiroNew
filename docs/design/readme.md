# SHADIRO - Design System Implementation Guide

## 🎨 Overview

This is the **Phase 0: Foundation Setup** for Shadiro, the premium event marketplace platform. The design system is fully configured and ready for team use.

### What's Been Completed

✅ **Design Tokens** - Colors, typography, spacing, shadows (all extracted to CSS variables)
✅ **Tailwind Configuration** - Extended with design system values
✅ **Component Foundation** - Button with 6 variants, Shadcn/UI base (43+ components)
✅ **Business Components** - VendorCard, PackageCard, ReviewCard, BookingCard
✅ **Design System Showcase** - Interactive reference page at `/design-system`
✅ **Documentation** - Comprehensive guides for developers

---

## 🚀 Quick Start

### 1. View the Design System

Navigate to `http://localhost:3000/design-system` to see:
- Color palette (Primary Blue, Accent Gold, Semantic colors)
- Typography system (H1 through Tiny)
- Spacing grid (xs to jumbo)
- All button variants and sizes
- Form components
- Complete interactive examples

### 2. Import Components

```javascript
// Base UI Components (from Shadcn/UI)
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

// Business Components
import { VendorCard } from '@/components/business';
import { PackageCard, PackageComparison } from '@/components/business';
import { ReviewCard, ReviewsList } from '@/components/business';
import { BookingCard, BookingsList } from '@/components/business';
```

### 3. Use Components

```jsx
// Simple button
<Button variant="primary" size="lg">
  Book Now
</Button>

// Vendor card with callback
<VendorCard
  vendor={vendorData}
  onSelect={handleSelect}
  onMessage={handleMessage}
/>

// Package list
<PackageComparison
  packages={packages}
  selectedId={selected}
  onSelect={handleSelect}
/>
```

---

## 🎨 Design System Overview

### Color Palette

| Color | Hex | Usage | CSS Class |
|-------|-----|-------|-----------|
| **Primary Blue** | #2C5285 | Primary CTAs, links, trust | `bg-primary`, `text-primary` |
| **Accent Gold** | #D4AF37 | Premium features, highlights | `bg-accent`, `text-accent` |
| **Success** | hsl(142, 71%, 45%) | Confirmations, positive actions | `bg-success`, `text-success` |
| **Error** | hsl(0, 84%, 60%) | Errors, destructive actions | `bg-error`, `text-error` |
| **Warning** | hsl(38, 92%, 50%) | Cautions, attention needed | `bg-warning`, `text-warning` |
| **Neutral** | 50-900 scale | Text, borders, backgrounds | `text-foreground`, `bg-muted` |

### Typography

| Level | Size | Weight | Font | Usage |
|-------|------|--------|------|-------|
| H1 | 2.8rem | 700 | Playfair Display | Main page heading |
| H2 | 2.2rem | 700 | Playfair Display | Section heading |
| H3 | 1.75rem | 600 | Playfair Display | Subsection |
| H4-H6 | 1.5-1.1rem | 600 | Playfair Display | Minor headings |
| Body LG | 1.125rem | 400 | DM Sans | Large body text |
| Body MD | 1rem | 400 | DM Sans | Standard paragraph |
| Body SM | 0.875rem | 400 | DM Sans | Secondary text |
| Tiny | 0.75rem | 500 | DM Sans | Labels, captions |

**CSS Classes:**
```html
<!-- Headings -->
<h1 class="text-h1 font-heading">Main Title</h1>
<h2 class="text-h2 font-heading">Section</h2>

<!-- Body Text -->
<p class="text-body-md">Standard text</p>
<p class="text-body-sm">Secondary text</p>

<!-- Tiny Labels -->
<span class="text-tiny">Caption</span>
```

### Spacing System (8px Base Grid)

```css
/* All spacing uses multiples of 8px */
xs    → 4px    /* Minimal gaps */
sm    → 8px    /* Small padding */
md    → 16px   /* Standard padding */
lg    → 24px   /* Large padding */
xl    → 32px   /* Extra large */
jumbo → 48px   /* Jumbo spacing */

/* Usage in Tailwind */
p-md          /* padding: 16px */
m-lg          /* margin: 24px */
gap-sm        /* gap: 8px */
px-lg py-md   /* padding: 24px horizontal, 16px vertical */
```

### Shadows & Elevation

```css
shadow-sm          /* Subtle (cards) */
shadow-md          /* Default buttons hover */
shadow-lg          /* Hover state */
shadow-xl          /* High elevation */
shadow-premium     /* Premium blue shadow (featured cards) */
```

---

## 📦 Button Component

The button component is the foundation for all interactions.

### Variants

```jsx
// Primary - Main CTA (blue)
<Button variant="primary">Book Now</Button>

// Secondary - Alternative action (gray with border)
<Button variant="secondary">Learn More</Button>

// Premium - Prestige action (gold)
<Button variant="premium">Upgrade Plan</Button>

// Outline - Bordered alternative
<Button variant="outline">View Details</Button>

// Text - Subtle/tertiary action
<Button variant="text">Skip</Button>

// Danger - Destructive action (red)
<Button variant="danger">Cancel</Button>
```

### Sizes

```jsx
<Button size="xs">Extra Small (32px)</Button>
<Button size="sm">Small (36px)</Button>
<Button size="default">Standard (44px)</Button>  {/* Mobile standard */}
<Button size="lg">Large (48px)</Button>
<Button size="xl">Extra Large (56px)</Button>
<Button size="icon">Icon Only (40px)</Button>
```

### Interactive States

```jsx
{/* Hover, Active, Disabled states are automatic */}
<Button variant="primary">Hover me</Button>
<Button disabled>Disabled</Button>

// With loading state (controlled by parent)
<Button disabled={isLoading}>
  {isLoading ? 'Loading...' : 'Submit'}
</Button>
```

---

## 🧩 Business Components

### VendorCard

Display vendor information in grid or list layout.

```jsx
import { VendorCard } from '@/components/business';

<VendorCard
  vendor={{
    id: '1',
    name: 'Premium Photography Studio',
    category: 'Photography',
    location: 'Mumbai, Maharashtra',
    image: 'https://...',
    rating: 4.8,
    reviewCount: 245,
    isVerified: true,
    isFeatured: true,
  }}
  layout="grid"  // or "list"
  onClick={() => navigate(`/vendors/1`)}
  onMessage={() => openChat(vendorId)}
  onSave={() => saveFavorite(vendorId)}
/>
```

**Grid Layout (default):** 240px card with image, name, rating, quick actions
**List Layout:** Horizontal card with image on left, details on right, full width

### PackageCard

Show pricing tiers with features and selection.

```jsx
import { PackageCard, PackageComparison } from '@/components/business';

const packages = [
  {
    id: '1',
    name: 'Basic',
    price: 25000,
    duration: '4 hours',
    features: ['Photography', '200+ photos', 'Digital delivery'],
    isPopular: false,
  },
  {
    id: '2',
    name: 'Premium',
    price: 75000,
    duration: '12 hours',
    features: ['Photography', '500+ photos', 'Video', 'Album'],
    isPopular: true,
  },
];

<PackageComparison
  packages={packages}
  selectedId={selectedPackageId}
  onSelect={(pkg) => setSelectedPackageId(pkg.id)}
/>
```

### ReviewCard

Display user reviews with vendor replies.

```jsx
import { ReviewCard, ReviewsList } from '@/components/business';

<ReviewsList
  reviews={reviews}
  onReply={(reviewId, text) => submitReply(reviewId, text)}
  onHelpful={(reviewId, isHelpful) => toggleHelpful(reviewId, isHelpful)}
  onReport={(reviewId) => reportReview(reviewId)}
/>
```

### BookingCard

Show booking status and quick actions.

```jsx
import { BookingCard, BookingsList } from '@/components/business';

<BookingsList
  bookings={bookings}
  onChat={() => openChat(bookingVendorId)}
  onReschedule={() => openRescheduleModal(bookingId)}
  onCancel={() => confirmCancel(bookingId)}
  onRate={() => openRatingModal(bookingId)}
/>
```

---

## 🎯 Common Patterns

### Form Field with Label

```jsx
<div className="space-y-2">
  <label className="text-body-sm font-medium text-foreground">
    Full Name
  </label>
  <Input
    placeholder="Enter your name"
    className="h-11"  // 44px for mobile standard
  />
</div>
```

### Card Layout

```jsx
<Card className="shadow-md hover:shadow-lg transition-all">
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    <p className="text-body-md">Content goes here</p>
  </CardContent>
</Card>
```

### Badge Group

```jsx
<div className="flex flex-wrap gap-2">
  <Badge className="bg-primary/10 text-primary">Verified</Badge>
  <Badge className="bg-accent/10 text-accent">Featured</Badge>
  <Badge className="bg-success/10 text-success">Popular</Badge>
</div>
```

### Grid Responsive

```jsx
{/* Responsive grid that adapts to screen size */}
<div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-lg">
  {items.map(item => <VendorCard key={item.id} vendor={item} />)}
</div>
```

### Container with Padding

```jsx
<div className="max-w-7xl mx-auto px-md md:px-lg py-xl">
  <h1 className="text-h1 font-heading mb-xl">Page Title</h1>
  {/* Content */}
</div>
```

---

## 📱 Responsive Design

The design system uses mobile-first approach with Tailwind breakpoints:

```
xs: 0px        → Mobile phones
sm: 640px      → Small tablets
md: 768px      → Tablets
lg: 1024px     → Desktops
xl: 1280px     → Large desktops
2xl: 1536px    → Extra large monitors
```

### Example

```jsx
{/* Single column on mobile, 2 on tablet, 4 on desktop */}
<div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-lg">
  {/* Items */}
</div>

{/* Text sizing */}
<p className="text-body-md md:text-body-lg lg:text-h6">
  Responsive text
</p>

{/* Padding */}
<div className="p-md md:p-lg lg:p-xl">
  Responsive padding
</div>
```

---

## 🎨 Customizing Components

### Override Styles

```jsx
// Add Tailwind classes
<Button className="bg-accent text-foreground hover:bg-accent-dark">
  Custom Button
</Button>

// Combine variants
<Button variant="primary" size="lg" className="w-full">
  Full width button
</Button>
```

### Custom Card

```jsx
<Card className="border-2 border-primary shadow-premium">
  <CardHeader>
    <CardTitle>Featured</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

---

## 🚨 Common Mistakes to Avoid

❌ **Don't:** Use hardcoded colors
```jsx
<Button className="bg-blue-500">  {/* Wrong */}
```

✅ **Do:** Use design tokens
```jsx
<Button variant="primary">  {/* Right */}
```

❌ **Don't:** Ignore responsive design
```jsx
<div className="w-1/4">  {/* Fixed width, breaks on mobile */}
```

✅ **Do:** Use responsive classes
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">  {/* Right */}
```

❌ **Don't:** Use random spacing
```jsx
<div className="mt-7 mb-13 px-11">  {/* Wrong */}
```

✅ **Do:** Use design system spacing
```jsx
<div className="mt-lg mb-xl px-md">  {/* Right */}
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `DESIGN_TOKENS_REFERENCE.js` | Complete design token documentation |
| `IMPLEMENTATION_PROGRESS_WEEK1.md` | Week 1 progress and roadmap |
| `src/pages/DesignSystemShowcase.js` | Interactive component showcase |
| `README.md` | This file - Quick start guide |

---

## 🔧 Development Workflow

### Adding a New Component

1. **Check the design spec** - Which component from design system?
2. **Choose base component** - Use Shadcn/UI or create custom?
3. **Use design tokens** - All colors, spacing, shadows from tokens
4. **Make it responsive** - Test on xs, sm, md, lg, xl
5. **Test accessibility** - Keyboard nav, ARIA, color contrast
6. **Add to showcase** - Include in design system page if high-level

### Example: Creating NewCard

```jsx
// 1. Import from design system
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// 2. Create component with design tokens
export const NewCard = ({ data, onAction, className }) => {
  return (
    <Card className={cn('overflow-hidden hover:shadow-lg transition-all', className)}>
      <CardHeader>
        <CardTitle className="text-h5 font-heading">{data.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-md">
        <p className="text-body-md text-foreground">{data.description}</p>
        <Badge className="bg-primary/10 text-primary">{data.status}</Badge>
        <Button variant="primary" onClick={onAction} className="w-full">
          Action
        </Button>
      </CardContent>
    </Card>
  );
};
```

3. **Export** from `components/business/index.js`
4. **Test** on `/design-system` page
5. **Document** usage in this file

---

## 📊 Component Inventory

### ✅ Available Now

**UI Components (43+):**
- Button (6 variants, 6 sizes)
- Card, Input, Badge, Tabs, Dialog, Dropdown...

**Business Components (4):**
- VendorCard (grid/list layout)
- PackageCard (with comparison)
- ReviewCard (with replies)
- BookingCard (with status)

### 🏗️ Coming Soon

- ChatMessage
- EventTimeline
- QuoteCard
- PriceBreakdown
- BookingTimeline
- EmergencyBanner
- And 10+ more...

---

## ❓ FAQ

**Q: Where do I find the primary blue color?**
A: Use `bg-primary` or `text-primary`. It's #2C5285 (hsl(218, 50%, 35%)).

**Q: What's the default button size?**
A: `size="default"` = 44px height (mobile standard touch target).

**Q: How do I make a full-width button?**
A: Add `className="w-full"` to Button component.

**Q: Can I use custom colors?**
A: Avoid it. Update design tokens in `src/index.css` and `tailwind.config.js` instead.

**Q: How do I add a new semantic color?**
A: Update `--warning`, `--error` variables in `src/index.css` and tailwind config.

**Q: What if a component doesn't exist?**
A: Check `IMPLEMENTATION_PROGRESS_WEEK1.md` for roadmap. Create an issue if urgent.

---

## 🎓 Learning Resources

1. **Shadcn/UI Docs** - Component API reference
2. **Tailwind CSS Docs** - Utility class reference
3. **Design System Showcase** - Interactive examples (http://localhost:3000/design-system)
4. **DESIGN_TOKENS_REFERENCE.js** - Token documentation

---

## 📞 Support

For questions or issues:
1. Check this README first
2. Check `DESIGN_TOKENS_REFERENCE.js`
3. Review component examples in `/design-system`
4. Check existing component implementations
5. Post in team Slack/Discord

---

## ✅ Checklist for Team

Before using components in your features:

- [ ] Read this README
- [ ] Visit `/design-system` page
- [ ] Check `DESIGN_TOKENS_REFERENCE.js`
- [ ] Review similar existing components
- [ ] Test on mobile (xs: < 640px)
- [ ] Test on tablet (sm: 640px - 1024px)
- [ ] Test on desktop (lg: > 1024px)
- [ ] Verify color contrast (WCAG AA)
- [ ] Check focus states (keyboard nav)
- [ ] Test with screen reader (if involved)

---

**Last Updated:** 2024  
**Next Update:** End of Week 2  
**Owner:** Design & Frontend Team
