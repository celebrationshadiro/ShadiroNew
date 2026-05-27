import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Check, Star, Zap } from 'lucide-react';

/**
 * PackageCard Component
 * 
 * Displays vendor package/pricing options with:
 * - Package tier (Basic, Standard, Premium)
 * - Price and billing period
 * - Feature list with checkmarks
 * - Popular/recommended badge
 * - CTA button
 * - Responsive grid layout
 * 
 * @component
 * @example
 * <PackageCard
 *   package={packageData}
 *   isSelected={selectedId === packageData.id}
 *   onSelect={handleSelect}
 *   isPacked={true}
 * />
 */

export const PackageCard = ({
  package: pkg = {},
  isSelected = false,
  isPopular = false,
  onSelect,
  onCustomize,
  className,
}) => {
  // Default package data
  const packageData = {
    id: pkg.id || '1',
    name: pkg.name || 'Basic Package',
    description: pkg.description || 'Perfect for small events',
    price: pkg.price || 25000,
    currency: pkg.currency || '₹',
    billingPeriod: pkg.billingPeriod || 'per event',
    duration: pkg.duration || '4 hours',
    features: pkg.features || [
      'Photography coverage',
      '200+ edited photos',
      'Digital delivery',
      'Cloud backup',
    ],
    limitations: pkg.limitations || [
      'Video not included',
      'Print album extra',
    ],
    discount: pkg.discount || 0,
    isPopular: isPopular,
  };

  const discountedPrice = packageData.price * (1 - packageData.discount / 100);

  return (
    <Card
      className={cn(
        'overflow-hidden flex flex-col h-full transition-all duration-300 cursor-pointer',
        isSelected && 'ring-2 ring-primary shadow-lg',
        packageData.isPopular && 'shadow-premium border-accent/30',
        !isSelected && 'hover:shadow-md hover:border-primary/20',
        className
      )}
      onClick={() => onSelect?.(packageData)}
    >
      {/* Popular Badge */}
      {packageData.isPopular && (
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-accent to-accent-dark text-accent-foreground py-2 px-4 flex items-center justify-center gap-2 z-10">
          <Zap size={16} />
          <span className="text-tiny font-semibold">RECOMMENDED</span>
        </div>
      )}

      {/* Header with offset for popular badge */}
      <CardHeader className={cn('pb-3', packageData.isPopular && 'pt-12')}>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-h5 font-heading">
              {packageData.name}
            </CardTitle>
            {isSelected && (
              <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                <Check size={16} className="font-bold" />
              </div>
            )}
          </div>
          <p className="text-body-sm text-muted-foreground">
            {packageData.description}
          </p>
        </div>
      </CardHeader>

      {/* Pricing */}
      <CardContent className="space-y-6 flex-1 flex flex-col">
        <div className="space-y-1">
          <div className="flex items-baseline gap-2">
            <span className="text-h4 font-bold text-primary">
              {packageData.currency}
              {discountedPrice.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </span>
            {packageData.discount > 0 && (
              <>
                <span className="text-body-sm text-muted-foreground line-through">
                  {packageData.currency}
                  {packageData.price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
                <Badge className="bg-error/10 text-error">{packageData.discount}% OFF</Badge>
              </>
            )}
          </div>
          <p className="text-body-sm text-muted-foreground">
            {packageData.billingPeriod}
          </p>
          {packageData.duration && (
            <p className="text-tiny text-muted-foreground">
              Duration: {packageData.duration}
            </p>
          )}
        </div>

        {/* Divider */}
        <div className="h-px bg-border"></div>

        {/* Features */}
        <div className="space-y-3 flex-1">
          <h4 className="text-body-sm font-semibold text-foreground">What's Included:</h4>
          <ul className="space-y-2">
            {packageData.features.map((feature, idx) => (
              <li key={idx} className="flex items-start gap-2 text-body-sm">
                <Check size={16} className="text-success mt-0.5 flex-shrink-0" />
                <span className="text-foreground">{feature}</span>
              </li>
            ))}
          </ul>

          {packageData.limitations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <h4 className="text-body-sm font-semibold text-muted-foreground mb-2">
                Not Included:
              </h4>
              <ul className="space-y-1">
                {packageData.limitations.map((limite, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-body-sm text-muted-foreground">
                    <span className="text-error mt-1">−</span>
                    <span>{limite}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="h-px bg-border"></div>

        {/* Actions */}
        <div className="pt-2 space-y-2">
          <Button
            variant={isSelected ? 'primary' : packageData.isPopular ? 'premium' : 'outline'}
            size="lg"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.(packageData);
            }}
          >
            {isSelected ? 'Selected' : 'Select Package'}
          </Button>
          {onCustomize && (
            <Button
              variant="text"
              size="sm"
              className="w-full"
              onClick={(e) => {
                e.stopPropagation();
                onCustomize?.(packageData);
              }}
            >
              Customize Package
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * PackageComparison Component
 * Displays multiple packages side-by-side for comparison
 */
export const PackageComparison = ({
  packages = [],
  selectedId = null,
  onSelect,
  className,
}) => {
  return (
    <div className={cn('space-y-4', className)}>
      <h3 className="text-h4 font-heading">Choose Your Package</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {packages.map((pkg, idx) => (
          <PackageCard
            key={pkg.id || idx}
            package={pkg}
            isSelected={selectedId === pkg.id}
            isPopular={pkg.isPopular}
            onSelect={onSelect}
          />
        ))}
      </div>

      {/* Info Text */}
      <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-6">
        <p className="text-body-sm text-foreground">
          <span className="font-semibold">Need a custom package?</span> Contact the vendor directly to discuss your requirements and get a personalized quote.
        </p>
      </div>
    </div>
  );
};

export default PackageCard;
