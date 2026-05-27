/**
 * SHADIRO DESIGN SYSTEM - IMPLEMENTATION REFERENCE
 * 
 * This file documents all design tokens used throughout the Shadiro platform.
 * These tokens are defined in src/index.css and configured in tailwind.config.js
 * 
 * @version 1.0.0
 * @lastUpdated 2024
 */

// ============================================================================
// COLOR PALETTE
// ============================================================================

const COLORS = {
  // PRIMARY: Deep Blue (#2C5285)
  // Used for: Primary CTAs, links, important text, trust signals
  primary: {
    DEFAULT: "hsl(218, 50%, 35%)",     // #2C5285
    light: "hsl(218, 50%, 45%)",       // Hover state
    dark: "hsl(218, 50%, 25%)",        // Active/pressed state
    50: "hsl(218, 100%, 97%)",         // Lightest (backgrounds)
    100: "hsl(218, 100%, 95%)",
    200: "hsl(218, 100%, 90%)",
    300: "hsl(218, 80%, 70%)",
    400: "hsl(218, 60%, 50%)",
    500: "hsl(218, 50%, 40%)",
    600: "hsl(218, 50%, 35%)",         // Base
    700: "hsl(218, 50%, 30%)",
    800: "hsl(218, 50%, 25%)",
    900: "hsl(218, 50%, 20%)",
  },

  // ACCENT: Gold (#D4AF37)
  // Used for: Premium features, highlights, prestige elements, secondary CTAs
  accent: {
    DEFAULT: "hsl(45, 75%, 52%)",      // #D4AF37
    light: "hsl(45, 75%, 62%)",        // Hover state
    dark: "hsl(45, 75%, 42%)",         // Active/pressed state
    50: "hsl(45, 100%, 95%)",
    100: "hsl(45, 100%, 92%)",
    200: "hsl(45, 100%, 85%)",
    300: "hsl(45, 90%, 70%)",
    400: "hsl(45, 80%, 60%)",
    500: "hsl(45, 75%, 52%)",          // Base
    600: "hsl(45, 75%, 45%)",
    700: "hsl(45, 75%, 38%)",
    800: "hsl(45, 75%, 32%)",
  },

  // SEMANTIC COLORS
  // Used for: Status indication, feedback, validation
  semantic: {
    success: {
      DEFAULT: "hsl(142, 71%, 45%)",   // Green - Confirmation
      light: "hsl(142, 71%, 55%)",
      dark: "hsl(142, 71%, 35%)",
    },
    warning: {
      DEFAULT: "hsl(38, 92%, 50%)",    // Amber - Caution
      light: "hsl(38, 92%, 60%)",
      dark: "hsl(38, 92%, 40%)",
    },
    error: {
      DEFAULT: "hsl(0, 84%, 60%)",     // Red - Error/Danger
      light: "hsl(0, 84%, 70%)",
      dark: "hsl(0, 84%, 50%)",
    },
    info: {
      DEFAULT: "hsl(200, 100%, 50%)",  // Cyan - Information
      light: "hsl(200, 100%, 60%)",
      dark: "hsl(200, 100%, 40%)",
    },
  },

  // NEUTRAL PALETTE
  // Used for: Text, backgrounds, borders
  neutral: {
    50: "hsl(0, 0%, 99%)",             // Almost white (light backgrounds)
    100: "hsl(0, 0%, 97%)",            // Very light (alternate backgrounds)
    200: "hsl(0, 0%, 93%)",            // Light (disabled states, borders)
    300: "hsl(0, 0%, 89%)",            // Light borders
    400: "hsl(0, 0%, 85%)",
    500: "hsl(0, 0%, 70%)",            // Medium gray
    600: "hsl(0, 0%, 50%)",
    700: "hsl(0, 0%, 35%)",            // Dark text
    800: "hsl(0, 0%, 20%)",
    900: "hsl(0, 0%, 11%)",            // Almost black (foreground)
  },

  // DEPRECATED (kept for reference - use primary/accent instead)
  // previous: {
  //   primary: "#BE185D",
  //   secondary: "#F59E0B",
  //   accent: "#8B5CF6",
  // }
};

// ============================================================================
// TYPOGRAPHY SYSTEM
// ============================================================================

const TYPOGRAPHY = {
  // Font Families
  fonts: {
    heading: "'Playfair Display', serif",      // Headlines, titles
    body: "'DM Sans', sans-serif",             // Body text, UI
  },

  // Font Sizes & Scales
  sizes: {
    h1: {
      fontSize: "2.8rem",
      lineHeight: "1.2",
      fontWeight: "700",
      letterSpacing: "-0.02em",
      // iOS: 28pt, Weight: Bold
    },
    h2: {
      fontSize: "2.2rem",
      lineHeight: "1.3",
      fontWeight: "700",
      letterSpacing: "-0.01em",
    },
    h3: {
      fontSize: "1.75rem",
      lineHeight: "1.35",
      fontWeight: "600",
    },
    h4: {
      fontSize: "1.5rem",
      lineHeight: "1.4",
      fontWeight: "600",
    },
    h5: {
      fontSize: "1.25rem",
      lineHeight: "1.4",
      fontWeight: "600",
    },
    h6: {
      fontSize: "1.1rem",
      lineHeight: "1.45",
      fontWeight: "600",
    },
    "body-lg": {
      fontSize: "1.125rem",
      lineHeight: "1.6",
      fontWeight: "400",
    },
    "body-md": {
      fontSize: "1rem",
      lineHeight: "1.6",
      fontWeight: "400",
      // iOS: 16pt (standard)
    },
    "body-sm": {
      fontSize: "0.875rem",
      lineHeight: "1.5",
      fontWeight: "400",
    },
    tiny: {
      fontSize: "0.75rem",
      lineHeight: "1.4",
      fontWeight: "500",
      // Captions, badges
    },
  },

  // Font Weights
  weights: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

// ============================================================================
// SPACING SYSTEM (8px Base Grid)
// ============================================================================

const SPACING = {
  xs: "0.25rem",    // 4px   - Minimal gaps
  sm: "0.5rem",     // 8px   - Small padding, gaps
  md: "1rem",       // 16px  - Standard padding
  lg: "1.5rem",     // 24px  - Section padding
  xl: "2rem",       // 32px  - Large section padding
  "2xl": "2.5rem",  // 40px  - Extra large gaps
  "3xl": "3rem",    // 48px  - Jumbo spacing
  "4xl": "4rem",    // 64px - Major sections
  
  // Common combinations
  padding: {
    field: "0.75rem",      // 12px (button/input padding)
    section: "1.5rem",     // 24px (vertical section spacing)
    page: "2rem",          // 32px (page padding on desktop)
    mobile: "1rem",        // 16px (mobile page padding)
  },
  
  gap: {
    input: "0.5rem",       // 8px (label to input)
    form: "1.5rem",        // 24px (between form fields)
    list: "1rem",          // 16px (between list items)
  },
};

// ============================================================================
// ELEVATION & SHADOWS
// ============================================================================

const SHADOWS = {
  // Elevation levels (from Design System)
  sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1)",
  
  // Premium shadow (primary blue with elevated depth)
  premium: "0 10px 40px -10px rgb(44 82 133 / 0.2)",
  
  // Hover elevations
  none: "none",
  inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

const BORDER_RADIUS = {
  micro: "0.125rem",  // 2px   - Smallest (checkboxes)
  sm: "0.375rem",     // 6px   - Small (badges)
  md: "0.5rem",       // 8px   - Medium (inputs, buttons)
  lg: "0.75rem",      // 12px  - Large (cards, modals)
  xl: "1rem",         // 16px  - Extra large (featured cards)
  full: "9999px",     // Full  - Circular/pill-shaped
};

// ============================================================================
// COMPONENT SIZES & DIMENSIONS
// ============================================================================

const COMPONENT_SIZES = {
  // Button Heights (standard for 44px touch target on mobile)
  button: {
    xs: "2rem",        // 32px
    sm: "2.25rem",     // 36px
    default: "2.75rem", // 44px (standard)
    lg: "3rem",        // 48px
    xl: "3.5rem",      // 56px
  },

  // Input Heights
  input: {
    sm: "2rem",        // 32px
    default: "2.75rem", // 44px
    lg: "3rem",        // 48px
  },

  // Icon Sizes
  icon: {
    xs: "1rem",        // 16px
    sm: "1.5rem",      // 24px
    default: "1.5rem", // 24px
    md: "2rem",        // 32px
    lg: "2.5rem",      // 40px
    xl: "3rem",        // 48px
  },

  // Card Widths
  card: {
    full: "100%",
    viewport: "100vw",
    container: "1200px",
    mobile: "100%",
    tablet: "800px",
    desktop: "1200px",
  },
};

// ============================================================================
// TRANSITIONS & ANIMATIONS
// ============================================================================

const ANIMATIONS = {
  duration: {
    fast: "150ms",
    base: "200ms",
    slow: "300ms",
  },
  
  easing: {
    linear: "linear",
    in: "cubic-bezier(0.4, 0, 1, 1)",
    out: "cubic-bezier(0, 0, 0.2, 1)",
    inOut: "cubic-bezier(0.4, 0, 0.2, 1)",
  },
  
  premiumAnimations: {
    fadeIn: "fade-in 300ms ease-out",
    slideUp: "slide-up 300ms ease-out",
    scaleIn: "scale-in 200ms ease-out",
    spinnerRotate: "spinner 1s linear infinite",
  },
};

// ============================================================================
// RESPONSIVE BREAKPOINTS
// ============================================================================

const BREAKPOINTS = {
  xs: "0px",          // Mobile (phones)
  sm: "640px",        // Small tablets
  md: "768px",        // Tablets
  lg: "1024px",       // Desktops
  xl: "1280px",       // Large desktops
  "2xl": "1536px",    // Extra large desktops
};

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

const USAGE_EXAMPLES = {
  primaryButton: {
    bg: "bg-primary",
    text: "text-primary-foreground",
    hover: "hover:bg-primary-light",
    active: "active:bg-primary-dark",
    shadow: "shadow-md hover:shadow-lg",
  },

  premiumCard: {
    bg: "bg-card",
    border: "border border-primary/10",
    shadow: "shadow-lg hover:shadow-premium",
    padding: "p-lg",
    borderRadius: "rounded-lg",
  },

  textBase: {
    font: "font-body",
    size: "text-body-md",
    lineHeight: "leading-relaxed",
    color: "text-foreground",
  },

  headingBase: {
    font: "font-heading",
    weight: "font-bold",
    color: "text-foreground",
  },

  formField: {
    input: "border border-input rounded-md h-11 px-4 py-2 text-body-md",
    label: "text-body-sm font-medium text-foreground mb-sm",
    error: "text-error text-body-sm mt-xs",
  },

  badge: {
    base: "inline-flex items-center rounded-full px-3 py-1 text-tiny font-medium",
    primary: "bg-primary/10 text-primary",
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
    danger: "bg-error/10 text-error",
  },
};

// ============================================================================
// EXPORT
// ============================================================================

export default {
  COLORS,
  TYPOGRAPHY,
  SPACING,
  SHADOWS,
  BORDER_RADIUS,
  COMPONENT_SIZES,
  ANIMATIONS,
  BREAKPOINTS,
  USAGE_EXAMPLES,
};

/**
 * IMPLEMENTATION CHECKLIST
 * 
 * ✅ Design tokens extracted to CSS variables (index.css)
 * ✅ Tailwind configuration updated with tokens (tailwind.config.js)
 * ✅ Button component updated with 6 variants
 * ✅ Spacing system configured (8px base grid)
 * ✅ Typography scales defined (H1-Tiny)
 * ✅ Color palette standardized (Primary Blue, Accent Gold, Semantic)
 * ⏳ Next: Create component showcase app
 * ⏳ Next: Build business components (VendorCard, PackageCard, etc.)
 * ⏳ Next: Create example pages (Auth, Home, Detail)
 * 
 * QUICK CSS CLASS REFERENCE
 * 
 * Colors:
 *   Text: text-primary, text-secondary, text-accent
 *   BG: bg-primary, bg-accent, bg-card, bg-muted
 *   Semantic: text-success, text-error, text-warning
 * 
 * Typography:
 *   Headings: text-h1, text-h2, text-h3, text-h4, text-h5, text-h6
 *   Body: text-body-lg, text-body-md, text-body-sm, text-tiny
 *   Font: font-heading, font-body
 * 
 * Spacing (8px grid):
 *   xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, jumbo: 48px
 *   Examples: p-md (padding), m-lg (margin), gap-sm (gap)
 * 
 * Shadows:
 *   shadow-sm, shadow-md, shadow-lg, shadow-xl, shadow-premium
 * 
 * Rounding:
 *   rounded-micro, rounded-sm, rounded-md, rounded-lg, rounded-xl, rounded-full
 * 
 * Button Variants:
 *   variant: primary | secondary | text | outline | premium | danger | ghost | link
 *   size: xs | sm | default | lg | xl | icon | icon-sm
 */
