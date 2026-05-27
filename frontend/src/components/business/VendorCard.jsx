import React, { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Heart, MapPin, Star, Verified, MessageSquare } from 'lucide-react';

/**
 * VendorCard Component
 * 
 * Displays vendor information in a card format with:
 * - Hero image with category badge
 * - Vendor info (name, location, rating)
 * - Verified badge and metrics
 * - Quick actions (view, message, save)
 * - Responsive design (grid/list variants)
 * 
 * @component
 * @example
 * <VendorCard
 *   vendor={vendorData}
 *   layout="grid"
 *   onClick={handleViewVendorDetail}
 *   onMessage={handleOpenChat}
 * />
 */

export const VendorCard = ({
  vendor = {},
  layout = 'grid', // 'grid' or 'list'
  onClick,
  onMessage,
  onSave,
  className,
}) => {
  const [isSaved, setIsSaved] = useState(vendor.isSaved || false);

  const handleSave = (e) => {
    e.stopPropagation();
    setIsSaved(!isSaved);
    onSave?.(vendor);
  };

  // Default vendor data for demo
  const vendorData = {
    id: vendor.id || '1',
    name: vendor.name || 'Premium Photography Studio',
    category: vendor.category || 'Photography',
    location: vendor.location || 'Mumbai, Maharashtra',
    image: vendor.image || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=500&h=500&fit=crop',
    rating: vendor.rating || 4.8,
    reviewCount: vendor.reviewCount || 245,
    isVerified: vendor.isVerified !== false,
    isFeatured: vendor.isFeatured || false,
    maxPrice: vendor.maxPrice || '₹150,000',
    availability: vendor.availability || 'Available',
    metrics: vendor.metrics || {
      bookings: 342,
      satisfaction: 98,
      responseTime: '< 2 hours',
    },
  };

  if (layout === 'list') {
    return <ListVendorCard vendor={vendorData} onClick={onClick} onMessage={onMessage} isSaved={isSaved} onSave={handleSave} className={className} />;
  }

  return (
    <Card
      className={cn(
        'overflow-hidden h-full flex flex-col cursor-pointer group hover:shadow-lg transition-all duration-300 hover:border-primary/30',
        className
      )}
      onClick={onClick}
    >
      {/* Image Container */}
      <div className="relative h-48 bg-muted overflow-hidden">
        <img
          src={vendorData.image}
          alt={vendorData.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        
        {/* Badges */}
        <div className="absolute top-3 left-3 right-3 flex flex-wrap gap-2">
          <Badge variant="default" className="bg-primary text-primary-foreground">
            {vendorData.category}
          </Badge>
          {vendorData.isFeatured && (
            <Badge className="bg-accent text-accent-foreground">Featured</Badge>
          )}
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          className={cn(
            'absolute top-3 right-3 w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200',
            isSaved
              ? 'bg-error text-error-foreground shadow-md'
              : 'bg-background/80 text-foreground hover:bg-background/95'
          )}
          aria-label={isSaved ? 'Remove from favorites' : 'Add to favorites'}
        >
          <Heart size={18} fill={isSaved ? 'currentColor' : 'none'} />
        </button>
      </div>

      {/* Content */}
      <CardContent className="flex flex-col flex-1 p-4 space-y-3">
        {/* Name & Verified Badge */}
        <div className="space-y-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-h6 font-heading text-foreground line-clamp-2">
              {vendorData.name}
            </h3>
            {vendorData.isVerified && (
              <Verified size={18} className="text-success flex-shrink-0 mt-0.5" />
            )}
          </div>
        </div>

        {/* Location */}
        <div className="flex items-center gap-1 text-body-sm text-muted-foreground">
          <MapPin size={16} className="flex-shrink-0" />
          <span className="line-clamp-1">{vendorData.location}</span>
        </div>

        {/* Rating */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Star size={16} className="text-accent fill-accent" />
            <span className="font-semibold text-foreground text-body-sm">
              {vendorData.rating}
            </span>
          </div>
          <span className="text-body-sm text-muted-foreground">
            ({vendorData.reviewCount} reviews)
          </span>
        </div>

        {/* Price Range */}
        <div className="pt-2 border-t border-border">
          <p className="text-body-sm text-muted-foreground">Starting from</p>
          <p className="text-body-lg font-semibold text-primary">
            {vendorData.maxPrice}
          </p>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-2 pt-2 mt-auto">
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              onClick?.();
            }}
          >
            View Details
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              onMessage?.();
            }}
          >
            <MessageSquare size={16} />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * ListVendorCard Component
 * Horizontal layout variant for vendor listing
 */
const ListVendorCard = ({
  vendor,
  onClick,
  onMessage,
  isSaved,
  onSave,
  className,
}) => {
  return (
    <Card
      className={cn(
        'overflow-hidden cursor-pointer group hover:shadow-lg transition-all duration-300 hover:border-primary/30',
        className
      )}
      onClick={onClick}
    >
      <div className="flex gap-4">
        {/* Image */}
        <div className="w-40 h-40 flex-shrink-0 bg-muted overflow-hidden">
          <img
            src={vendor.image}
            alt={vendor.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        </div>

        {/* Content */}
        <CardContent className="flex-1 py-4 pr-4 flex flex-col justify-between">
          {/* Name & Badges */}
          <div>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1">
                <h3 className="text-h6 font-heading text-foreground">
                  {vendor.name}
                </h3>
              </div>
              <button
                onClick={onSave}
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-200',
                  isSaved
                    ? 'bg-error text-error-foreground'
                    : 'bg-muted hover:bg-secondary text-foreground'
                )}
              >
                <Heart size={16} fill={isSaved ? 'currentColor' : 'none'} />
              </button>
            </div>

            {/* Location & Rating */}
            <div className="flex items-center gap-4 flex-wrap mb-2">
              <div className="flex items-center gap-1 text-body-sm text-muted-foreground">
                <MapPin size={14} />
                {vendor.location}
              </div>
              <div className="flex items-center gap-1">
                <Star size={16} className="text-accent fill-accent" />
                <span className="font-semibold text-body-sm">
                  {vendor.rating}
                </span>
                <span className="text-body-sm text-muted-foreground">
                  ({vendor.reviewCount})
                </span>
              </div>
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2 mb-3">
              {vendor.isVerified && (
                <Badge className="bg-success/10 text-success flex gap-1">
                  <Verified size={12} />
                  Verified Vendor
                </Badge>
              )}
              {vendor.isFeatured && (
                <Badge className="bg-accent/10 text-accent">Featured</Badge>
              )}
            </div>
          </div>

          {/* Metrics & CTA */}
          <div className="flex items-center justify-between">
            <div className="flex gap-4 text-body-sm text-muted-foreground">
              <div>
                <p className="font-semibold text-foreground">{vendor.metrics.bookings}</p>
                <p className="text-tiny">Bookings</p>
              </div>
              <div>
                <p className="font-semibold text-foreground">{vendor.metrics.satisfaction}%</p>
                <p className="text-tiny">Satisfaction</p>
              </div>
              <div>
                <p className="font-semibold text-foreground">{vendor.metrics.responseTime}</p>
                <p className="text-tiny">Response Time</p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onClick?.();
                }}
              >
                View Details
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onMessage?.();
                }}
              >
                <MessageSquare size={16} />
              </Button>
            </div>
          </div>
        </CardContent>
      </div>
    </Card>
  );
};

export default VendorCard;
