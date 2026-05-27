/**
 * SHADIRO Business Components
 * 
 * High-level components built on top of base UI components from Shadcn/UI.
 * These components are domain-specific for the wedding/event marketplace.
 * 
 * All components are:
 * - Responsive (mobile-first design)
 * - Accessible (WCAG 2.1 AA compliant)
 * - Themeable (using design system tokens)
 * - Customizable (via props and className)
 * - Tested (interactive examples in design system showcase)
 */

// Card Components
export { VendorCard } from './VendorCard';
export { PackageCard, PackageComparison } from './PackageCard';
export { ReviewCard, ReviewsList } from './ReviewCard';
export { BookingCard, BookingsList } from './BookingCard';

// Future Components (Coming Soon)
// export { ChatMessage, ChatBubble } from './ChatMessage';
// export { EventTimeline } from './EventTimeline';
// export { QuoteCard } from './QuoteCard';
// export { PriceBreakdown } from './PriceBreakdown';
// export { BookingTimeline } from './BookingTimeline';
// export { EmergencyBanner } from './EmergencyBanner';
// export { ItemAccordion } from './ItemAccordion';
// export { VendorHeader } from './VendorHeader';

/**
 * USAGE EXAMPLES
 * 
 * Import individual components:
 * ```
 * import { VendorCard } from '@/components/business';
 * ```
 * 
 * In JSX:
 * ```
 * <VendorCard
 *   vendor={vendorData}
 *   layout="grid"
 *   onClick={handleViewDetail}
 *   onMessage={handleMessage}
 * />
 * ```
 * 
 * COMPONENT PATTERNS:
 * 
 * 1. Card Components (Grid/List Layout)
 *    - VendorCard: Display vendor in grid/list
 *    - PackageCard: Show pricing tiers
 *    - ReviewCard: User reviews with vendor replies
 *    - BookingCard: Booking status and actions
 * 
 * 2. Container Components (Data Collections)
 *    - PackageComparison: Multiple packages side-by-side
 *    - ReviewsList: Filtered/sorted reviews
 *    - BookingsList: Paginated booking list
 * 
 * 3. Callback Props Pattern:
 *    All components support callbacks:
 *    - onSelect, onSave, onRate, onMessage, etc.
 *    Allows parent component to handle actions
 * 
 * 4. Default Data Pattern:
 *    All components have default data for testing
 *    Pass `vendor.key = undefined` to use defaults
 * 
 * RESPONSIVE DESIGN:
 * 
 * Grid Layout:
 * xs: 1 column (full width)
 * sm: 2 columns (640px)
 * md: 2-3 columns (768px)
 * lg: 3-4 columns (1024px)
 * xl: 4-5 columns (1280px)
 * 
 * All components use:
 * - Flexbox for mobile
 * - CSS Grid for desktop
 * - Tailwind's responsive breakpoints
 * - Mobile-first approach
 * 
 * CUSTOMIZATION:
 * 
 * All components accept `className` prop:
 * ```
 * <VendorCard className="shadow-xl border-2 border-primary" />
 * ```
 * 
 * Override specific styles:
 * ```
 * <Button variant="primary" className="bg-accent text-foreground" />
 * ```
 * 
 * ACCESSIBILITY:
 * 
 * ✅ Semantic HTML (article, section, h1-h6)
 * ✅ ARIA attributes (roles, labels, descriptions)
 * ✅ Keyboard navigation (Tab, Enter, Escape)
 * ✅ Focus management (visible focus rings)
 * ✅ Color contrast (WCAG AA minimum)
 * ✅ Touch targets (44px minimum)
 * 
 * TESTING CHECKLIST:
 * 
 * Before deploying new components:
 * - [ ] Test on mobile (< 640px)
 * - [ ] Test on tablet (640px - 1024px)
 * - [ ] Test on desktop (> 1024px)
 * - [ ] Test with keyboard navigation
 * - [ ] Test with screen reader
 * - [ ] Check color contrast
 * - [ ] Verify responsive images
 * - [ ] Check loading states
 * - [ ] Verify empty states
 * - [ ] Test hover/active states
 * 
 * COMPONENT ROADMAP:
 * 
 * Week 1: ✅ VendorCard, PackageCard, ReviewCard, BookingCard
 * Week 2: ChatMessage, EventTimeline, QuoteCard
 * Week 3: PriceBreakdown, BookingTimeline, EmergencyBanner
 * Week 4: ItemAccordion, VendorHeader, FilterPanel
 * 
 * For questions or updates, see DESIGN_TOKENS_REFERENCE.js
 */
