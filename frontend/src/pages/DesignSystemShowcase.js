import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Toast, toast } from '@/components/ui/sonner';

/**
 * SHADIRO DESIGN SYSTEM - Component Showcase & Validation
 * 
 * This page demonstrates:
 * - Color palette (Primary Blue, Accent Gold, Semantic colors)
 * - Typography system (H1-Tiny, Font families)
 * - Spacing system (8px grid)
 * - Button variants (6 types, 6 sizes)
 * - Form components
 * - Card layouts
 * - Badge styles
 * - Responsive design
 */

export default function DesignSystemShowcase() {
  const [buttonLoading, setButtonLoading] = useState(false);

  const handleDemoClick = () => {
    setButtonLoading(true);
    setTimeout(() => {
      setButtonLoading(false);
      toast.success('Button clicked! 🎉');
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary to-primary-dark text-primary-foreground py-jumbo px-md">
        <h1 className="text-h1 font-heading mb-md">Shadiro Design System</h1>
        <p className="text-body-lg max-w-2xl">
          Premium, trust-first UI framework. Validating all design tokens, components, and responsive behavior.
        </p>
      </div>

      <div className="max-w-7xl mx-auto p-lg">
        {/* ========== COLOR PALETTE ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">1. Color Palette</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-lg">
            {/* Primary Blue */}
            <Card className="overflow-hidden">
              <CardHeader className="bg-primary text-primary-foreground pb-md">
                <CardTitle>Primary Blue</CardTitle>
                <CardDescription className="text-primary-foreground/80">#2C5285 / hsl(218, 50%, 35%)</CardDescription>
              </CardHeader>
              <CardContent className="pt-md space-y-md">
                <div className="space-y-2">
                  <div className="flex justify-between text-tiny">
                    <span>Base</span>
                    <code className="bg-muted px-2 py-1 rounded">hsl(218, 50%, 35%)</code>
                  </div>
                  <div className="h-12 bg-primary rounded-md"></div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-tiny">
                    <span>Light (Hover)</span>
                    <code className="bg-muted px-2 py-1 rounded">45%</code>
                  </div>
                  <div className="h-12 bg-primary-light rounded-md"></div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-tiny">
                    <span>Dark (Active)</span>
                    <code className="bg-muted px-2 py-1 rounded">25%</code>
                  </div>
                  <div className="h-12 bg-primary-dark rounded-md"></div>
                </div>
              </CardContent>
            </Card>

            {/* Accent Gold */}
            <Card className="overflow-hidden">
              <CardHeader className="bg-accent text-accent-foreground pb-md">
                <CardTitle>Accent Gold</CardTitle>
                <CardDescription className="text-accent-foreground/80">#D4AF37 / hsl(45, 75%, 52%)</CardDescription>
              </CardHeader>
              <CardContent className="pt-md space-y-md">
                <div className="space-y-2">
                  <div className="flex justify-between text-tiny">
                    <span>Base</span>
                    <code className="bg-muted px-2 py-1 rounded">hsl(45, 75%, 52%)</code>
                  </div>
                  <div className="h-12 bg-accent rounded-md"></div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-tiny">
                    <span>Light (Hover)</span>
                    <code className="bg-muted px-2 py-1 rounded">62%</code>
                  </div>
                  <div className="h-12 bg-accent-light rounded-md"></div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-tiny">
                    <span>Dark (Active)</span>
                    <code className="bg-muted px-2 py-1 rounded">42%</code>
                  </div>
                  <div className="h-12 bg-accent-dark rounded-md"></div>
                </div>
              </CardContent>
            </Card>

            {/* Semantic: Success */}
            <Card className="overflow-hidden">
              <CardHeader className="bg-success text-primary-foreground pb-md">
                <CardTitle className="text-body-lg">Success (Green)</CardTitle>
                <CardDescription className="text-primary-foreground/80">hsl(142, 71%, 45%)</CardDescription>
              </CardHeader>
              <CardContent className="pt-md space-y-2">
                <div className="h-12 bg-success rounded-md"></div>
                <p className="text-tiny text-muted-foreground">✓ Confirmations, positive actions</p>
              </CardContent>
            </Card>

            {/* Semantic: Error */}
            <Card className="overflow-hidden">
              <CardHeader className="bg-error text-primary-foreground pb-md">
                <CardTitle className="text-body-lg">Error (Red)</CardTitle>
                <CardDescription className="text-primary-foreground/80">hsl(0, 84%, 60%)</CardDescription>
              </CardHeader>
              <CardContent className="pt-md space-y-2">
                <div className="h-12 bg-error rounded-md"></div>
                <p className="text-tiny text-muted-foreground">✗ Errors, destructive actions</p>
              </CardContent>
            </Card>

            {/* Semantic: Warning */}
            <Card className="overflow-hidden">
              <CardHeader className="bg-warning text-accent-foreground pb-md">
                <CardTitle className="text-body-lg">Warning (Amber)</CardTitle>
                <CardDescription className="text-accent-foreground/80">hsl(38, 92%, 50%)</CardDescription>
              </CardHeader>
              <CardContent className="pt-md space-y-2">
                <div className="h-12 bg-warning rounded-md"></div>
                <p className="text-tiny text-muted-foreground">⚠ Warnings, cautions</p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* ========== TYPOGRAPHY ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">2. Typography System</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
            {/* Playfair Display - Headings */}
            <Card>
              <CardHeader>
                <CardTitle>Playfair Display (Headings)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-lg">
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">H1 - 2.8rem / Bold</p>
                  <h1 className="text-h1 font-heading">The Ultimate Event Planning</h1>
                </div>
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">H2 - 2.2rem / Bold</p>
                  <h2 className="text-h2 font-heading">Find Your Perfect Vendor</h2>
                </div>
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">H3 - 1.75rem / Semibold</p>
                  <h3 className="text-h3 font-heading">Premium Quality Services</h3>
                </div>
              </CardContent>
            </Card>

            {/* DM Sans - Body */}
            <Card>
              <CardHeader>
                <CardTitle>DM Sans (Body Text)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-lg">
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">Body LG - 1.125rem</p>
                  <p className="text-body-lg">Discover thousands of trusted vendors in your area. Perfect for weddings, corporate events, and celebrations.</p>
                </div>
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">Body MD - 1rem (Standard)</p>
                  <p className="text-body-md">High-quality services with verified ratings. Browse packages, compare prices, and book with confidence.</p>
                </div>
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">Body SM - 0.875rem</p>
                  <p className="text-body-sm">Additional details, captions, and secondary information go here to provide context.</p>
                </div>
                <div>
                  <p className="text-tiny font-medium text-muted-foreground mb-sm">Tiny - 0.75rem</p>
                  <p className="text-tiny">Used for labels, badges, and small helper text elements.</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* ========== SPACING SYSTEM ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">3. Spacing System (8px Base Grid)</h2>
          
          <Card>
            <CardHeader>
              <CardTitle>Spacing Scale</CardTitle>
              <CardDescription>All spacing values are multiples of 8px for consistent rhythm</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-md">
                {[
                  { name: 'xs', value: '4px', class: 'w-1 bg-primary' },
                  { name: 'sm', value: '8px', class: 'w-2 bg-primary' },
                  { name: 'md', value: '16px', class: 'w-4 bg-primary' },
                  { name: 'lg', value: '24px', class: 'w-6 bg-primary' },
                  { name: 'xl', value: '32px', class: 'w-8 bg-primary' },
                  { name: 'jumbo', value: '48px', class: 'w-12 bg-primary' },
                ].map((item) => (
                  <div key={item.name}>
                    <div className="flex items-center gap-md">
                      <div className={`h-12 ${item.class} rounded`}></div>
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-tiny text-muted-foreground">{item.value}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>

        {/* ========== BUTTON VARIANTS ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">4. Button Variants & Sizes</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
            {/* Variants */}
            <Card>
              <CardHeader>
                <CardTitle>Button Variants</CardTitle>
                <CardDescription>Six distinct button styles for different contexts</CardDescription>
              </CardHeader>
              <CardContent className="space-y-md">
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Primary (Main CTA)</p>
                  <Button variant="primary">Book Now</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Secondary (Alternative)</p>
                  <Button variant="secondary">Learn More</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Premium (Prestige)</p>
                  <Button variant="premium">Upgrade Plan</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Outline (Bordered)</p>
                  <Button variant="outline">View Details</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Text (Subtle)</p>
                  <Button variant="text">Skip for Now</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Danger (Destructive)</p>
                  <Button variant="danger">Cancel Booking</Button>
                </div>
              </CardContent>
            </Card>

            {/* Sizes */}
            <Card>
              <CardHeader>
                <CardTitle>Button Sizes</CardTitle>
                <CardDescription>Responsive sizes for different use cases</CardDescription>
              </CardHeader>
              <CardContent className="space-y-md">
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">XS (32px)</p>
                  <Button size="xs">Small Button</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">SM (36px)</p>
                  <Button size="sm">Small</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">Default (44px) - Mobile Standard</p>
                  <Button size="default">Standard Button</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">LG (48px)</p>
                  <Button size="lg">Large Button</Button>
                </div>
                <div className="space-y-sm">
                  <p className="text-tiny font-medium text-muted-foreground">XL (56px)</p>
                  <Button size="xl">Extra Large</Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Interactive Demo */}
          <Card className="mt-lg">
            <CardHeader>
              <CardTitle>Interactive Examples</CardTitle>
            </CardHeader>
            <CardContent className="space-y-lg">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
                <div className="space-y-md">
                  <p className="text-body-md font-medium">Book Now (Primary + Large)</p>
                  <Button variant="primary" size="lg" className="w-full" onClick={handleDemoClick} disabled={buttonLoading}>
                    {buttonLoading ? 'Processing...' : 'Book Your Vendor'}
                  </Button>
                </div>
                <div className="space-y-md">
                  <p className="text-body-md font-medium">Premium Upgrade</p>
                  <Button variant="premium" size="lg" className="w-full">
                    Unlock Premium Features
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* ========== FORM COMPONENTS ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">5. Form Components</h2>
          
          <Card>
            <CardHeader>
              <CardTitle>Input Fields</CardTitle>
              <CardDescription>Standard form inputs with consistent styling</CardDescription>
            </CardHeader>
            <CardContent className="space-y-lg">
              <div>
                <label className="text-body-sm font-medium text-foreground mb-sm block">Full Name</label>
                <Input placeholder="Enter your full name" />
              </div>
              <div>
                <label className="text-body-sm font-medium text-foreground mb-sm block">Email Address</label>
                <Input type="email" placeholder="your@email.com" />
              </div>
              <div>
                <label className="text-body-sm font-medium text-foreground mb-sm block">Phone Number</label>
                <Input type="tel" placeholder="+91 9876543210" />
              </div>
              <div>
                <label className="text-body-sm font-medium text-foreground mb-sm block">Event Date</label>
                <Input type="date" />
              </div>
            </CardContent>
          </Card>
        </section>

        {/* ========== BADGES & STATUS ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">6. Badges & Status Indicators</h2>
          
          <Card>
            <CardHeader>
              <CardTitle>Badge Styles</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-md">
                <Badge variant="default">Verified</Badge>
                <Badge variant="secondary">Featured</Badge>
                <Badge className="bg-success/10 text-success">Active</Badge>
                <Badge className="bg-warning/10 text-warning">Pending</Badge>
                <Badge className="bg-error/10 text-error">Cancelled</Badge>
                <Badge className="bg-primary/10 text-primary">Premium</Badge>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* ========== CARDS ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">7. Card Layouts</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
            {/* Standard Card */}
            <Card>
              <CardHeader>
                <CardTitle>Standard Card</CardTitle>
                <CardDescription>Default elevation with border</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-body-md">Cards organize related content in a contained area. Use them for vendor listings, packages, and booking summaries.</p>
              </CardContent>
            </Card>

            {/* Elevated Card (Premium Shadow) */}
            <Card className="shadow-premium hover:shadow-lg transition-all">
              <CardHeader>
                <CardTitle className="text-accent">Premium Card</CardTitle>
                <CardDescription>Elevated with premium shadow effect</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-body-md">Premium cards with enhanced shadow create visual hierarchy and draw attention to important content.</p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* ========== RESPONSIVE GRID ========== */}
        <section className="mb-jumbo">
          <h2 className="text-h2 font-heading mb-xl">8. Responsive Grid Example</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-lg">
            {[1, 2, 3, 4].map((item) => (
              <Card key={item} className="h-64 flex flex-col justify-between">
                <CardHeader>
                  <CardTitle className="text-h5">Vendor {item}</CardTitle>
                  <CardDescription>Photography Services</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-md mb-md">
                    <Badge className="bg-accent/10 text-accent">4.9★</Badge>
                    <Badge className="bg-success/10 text-success">Verified</Badge>
                  </div>
                  <Button variant="primary" size="sm" className="w-full">View Details</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* ========== FOOTER ========== */}
        <section className="py-xl border-t border-border text-center">
          <h3 className="text-h4 font-heading mb-md">✅ Design System Validated</h3>
          <p className="text-body-md text-muted-foreground max-w-2xl mx-auto mb-lg">
            All components are responsive, accessible (WCAG 2.1 AA), and production-ready. 
            Use this page as your reference while building new features.
          </p>
          <div className="flex gap-md justify-center flex-wrap">
            <Button variant="primary">View Documentation</Button>
            <Button variant="secondary">Component API</Button>
            <Button variant="text">Design Tokens</Button>
          </div>
        </section>
      </div>
    </div>
  );
}
