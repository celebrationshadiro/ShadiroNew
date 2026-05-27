import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { VendorCard } from '@/components/business';
import { cn } from '@/lib/utils';
import { 
  Search, 
  ChevronRight, 
  Heart, 
  Star, 
  Sparkles,
  Camera,
  Utensils,
  Music,
  MapPin,
  Clock,
  CheckCircle
} from 'lucide-react';

/**
 * Home Page - Entry Point for Shadiro Platform
 * 
 * Features:
 * - Hero banner with search
 * - Category navigation
 * - Featured vendors
 * - Trust signals (reviews, verified vendors)
 * - Social proof (testimonials)
 * - Newsletter signup
 * - Mobile-optimized
 */

export default function HomePage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Recent searches for quick access
  const recentSearches = [
    'Wedding Photography',
    'Catering Services',
    'Venue Decoration',
    'DJ and Music',
  ];

  // Category navigation
  const categories = [
    {
      id: 'photography',
      name: 'Photography',
      icon: Camera,
      count: 342,
      color: 'from-blue-500 to-blue-600',
    },
    {
      id: 'catering',
      name: 'Catering',
      icon: Utensils,
      count: 287,
      color: 'from-orange-500 to-orange-600',
    },
    {
      id: 'music',
      name: 'Music & DJ',
      icon: Music,
      count: 156,
      color: 'from-purple-500 to-purple-600',
    },
    {
      id: 'venue',
      name: 'Venues',
      icon: MapPin,
      count: 98,
      color: 'from-red-500 to-red-600',
    },
  ];

  // Featured vendors (demo data)
  const featuredVendors = [
    {
      id: '1',
      name: 'Premium Photography Studio',
      category: 'Photography',
      image: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=500&h=500&fit=crop',
      rating: 4.9,
      reviewCount: 342,
      isVerified: true,
      isFeatured: true,
      maxPrice: '₹150,000',
      location: 'Mumbai, Maharashtra',
    },
    {
      id: '2',
      name: 'Gourmet Catering Co.',
      category: 'Catering',
      image: 'https://images.unsplash.com/photo-1504674900153-0cd76bcad816?w=500&h=500&fit=crop',
      rating: 4.7,
      reviewCount: 218,
      isVerified: true,
      isFeatured: true,
      maxPrice: '₹50,000',
      location: 'Mumbai, Maharashtra',
    },
    {
      id: '3',
      name: 'Elite DJ Services',
      category: 'Music & DJ',
      image: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=500&h=500&fit=crop',
      rating: 4.8,
      reviewCount: 196,
      isVerified: true,
      isFeatured: false,
      maxPrice: '₹80,000',
      location: 'Mumbai, Maharashtra',
    },
    {
      id: '4',
      name: 'Grand Ballroom Venue',
      category: 'Venues',
      image: 'https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=500&h=500&fit=crop',
      rating: 4.9,
      reviewCount: 267,
      isVerified: true,
      isFeatured: true,
      maxPrice: '₹5,00,000',
      location: 'Mumbai, Maharashtra',
    },
  ];

  // Testimonials
  const testimonials = [
    {
      name: 'Priya & Arjun',
      text: 'Amazing platform! Found our photographer within minutes. The entire team was professional and captured our special day beautifully.',
      rating: 5,
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
      event: 'Wedding',
    },
    {
      name: 'Sarah Kumar',
      text: 'Best experience planning my corporate event. The vendors were verified, prices were transparent, and booking was seamless.',
      rating: 5,
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      event: 'Corporate Event',
    },
    {
      name: 'Raj Patel',
      text: 'Contacted 3 vendors, got personalized quotes same day. The emergency support when my DJ cancelled was outstanding!',
      rating: 5,
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop',
      event: 'Birthday Party',
    },
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate('/vendors', { state: { search: searchQuery } });
    }
  };

  const handleCategoryClick = (category) => {
    navigate('/vendors', { state: { category: category.id } });
  };

  const handleVendorClick = (vendorId) => {
    navigate(`/vendors/${vendorId}`);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ========== HERO SECTION ========== */}
      <section className="relative bg-gradient-to-br from-primary via-primary-dark to-primary-dark text-primary-foreground overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 right-10 w-40 h-40 rounded-full bg-accent"></div>
          <div className="absolute bottom-20 left-10 w-60 h-60 rounded-full bg-accent opacity-50"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-md md:px-lg py-jumbo space-y-lg">
          {/* Main heading */}
          <div className="space-y-md">
            <h1 className="text-h1 font-heading leading-tight max-w-3xl">
              The Perfect Vendor For Your Perfect Event
            </h1>
            <p className="text-body-lg max-w-2xl">
              Discover and book 1000+ verified vendors for your wedding, birthday, corporate event, or celebration. 
              Transparent pricing • Instant quotes • Emergency support
            </p>
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="mt-xl max-w-2xl">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
                <Input
                  placeholder="Search vendors... (e.g., Wedding Photography, Catering)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-12 h-12 text-body-md focus:ring-accent"
                />
              </div>
              <Button
                type="submit"
                variant="premium"
                size="lg"
                className="px-xl"
              >
                Search
              </Button>
            </div>
          </form>

          {/* Recent searches */}
          {!searchQuery && (
            <div className="flex flex-wrap gap-2 mt-lg">
              <span className="text-body-sm opacity-80">Popular searches:</span>
              {recentSearches.map((search, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setSearchQuery(search);
                    navigate('/vendors', { state: { search } });
                  }}
                  className="px-4 py-2 bg-primary-foreground/10 hover:bg-primary-foreground/20 rounded-full text-body-sm transition-colors"
                >
                  {search}
                </button>
              ))}
            </div>
          )}

          {/* Trust signals */}
          <div className="flex flex-wrap gap-lg pt-xl border-t border-primary-foreground/20">
            <div className="flex items-center gap-2">
              <CheckCircle size={20} />
              <span className="text-body-md">10,000+ events booked</span>
            </div>
            <div className="flex items-center gap-2">
              <Star size={20} />
              <span className="text-body-md">4.8 average rating</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock size={20} />
              <span className="text-body-md">Same-day quotes</span>
            </div>
          </div>
        </div>
      </section>

      {/* ========== CATEGORIES SECTION ========== */}
      <section className="max-w-7xl mx-auto px-md md:px-lg py-xl">
        <h2 className="text-h3 font-heading mb-xl">Popular Categories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-lg">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <button
                key={category.id}
                onClick={() => handleCategoryClick(category)}
                className={cn(
                  'group relative overflow-hidden rounded-xl p-lg h-40 text-white transition-all duration-300',
                  'hover:shadow-lg hover:scale-105 active:scale-95',
                  `bg-gradient-to-br ${category.color}`
                )}
              >
                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors"></div>

                {/* Content */}
                <div className="relative h-full flex flex-col justify-between z-10">
                  <Icon size={32} />
                  <div className="text-left">
                    <h3 className="text-h5 font-semibold">{category.name}</h3>
                    <p className="text-body-sm opacity-90">{category.count} vendors</p>
                  </div>
                </div>

                {/* Hover arrow */}
                <div className="absolute right-4 bottom-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight size={24} />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* ========== FEATURED VENDORS SECTION ========== */}
      <section className="bg-muted py-xl">
        <div className="max-w-7xl mx-auto px-md md:px-lg space-y-xl">
          <div className="flex items-center justify-between gap-md">
            <div>
              <Badge className="bg-accent/10 text-accent mb-md flex gap-1 w-fit">
                <Sparkles size={14} />
                Featured
              </Badge>
              <h2 className="text-h3 font-heading">Top Rated Vendors</h2>
              <p className="text-body-md text-muted-foreground mt-sm">
                Trusted by thousands. Book with confidence.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => navigate('/vendors')}
              className="hidden sm:flex gap-2"
            >
              View All
              <ChevronRight size={16} />
            </Button>
          </div>

          {/* Vendors Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-lg">
            {featuredVendors.map((vendor) => (
              <VendorCard
                key={vendor.id}
                vendor={vendor}
                onClick={() => handleVendorClick(vendor.id)}
                onMessage={() => navigate(`/chat/${vendor.id}`)}
                onSave={() => {}}
              />
            ))}
          </div>

          {/* Mobile view all button */}
          <Button
            variant="primary"
            size="lg"
            className="w-full sm:hidden"
            onClick={() => navigate('/vendors')}
          >
            Browse All Vendors
          </Button>
        </div>
      </section>

      {/* ========== WHY CHOOSE US SECTION ========== */}
      <section className="max-w-7xl mx-auto px-md md:px-lg py-xl">
        <h2 className="text-h3 font-heading mb-xl text-center">Why Choose Shadiro?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
          {[
            {
              icon: CheckCircle,
              title: 'Verified Vendors',
              description: 'All vendors are verified with real reviews and ratings. 100% authentic.',
            },
            {
              icon: Clock,
              title: 'Instant Quotes',
              description: 'Get quotes from multiple vendors within hours. Compare prices side-by-side.',
            },
            {
              icon: Heart,
              title: 'Emergency Support',
              description: 'If a vendor cancels, we find a replacement. Your event is covered.',
            },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <Card key={idx} className="hover:shadow-lg transition-all">
                <CardContent className="p-lg space-y-md">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Icon size={24} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="text-h5 font-semibold mb-sm">{item.title}</h3>
                    <p className="text-body-md text-muted-foreground">{item.description}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ========== TESTIMONIALS SECTION ========== */}
      <section className="bg-gradient-to-br from-primary/5 to-accent/5 py-xl">
        <div className="max-w-7xl mx-auto px-md md:px-lg space-y-xl">
          <h2 className="text-h3 font-heading text-center">What Our Users Say</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
            {testimonials.map((testimonial, idx) => (
              <Card key={idx} className="overflow-hidden">
                <CardContent className="p-lg space-y-md">
                  {/* Rating */}
                  <div className="flex gap-1">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star
                        key={i}
                        size={16}
                        className="text-accent fill-accent"
                      />
                    ))}
                  </div>

                  {/* Review text */}
                  <p className="text-body-md text-foreground italic">
                    "{testimonial.text}"
                  </p>

                  {/* Reviewer info */}
                  <div className="pt-md border-t border-border flex items-center gap-3">
                    <img
                      src={testimonial.avatar}
                      alt={testimonial.name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                    <div>
                      <p className="font-semibold text-body-sm">{testimonial.name}</p>
                      <p className="text-tiny text-muted-foreground">{testimonial.event}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ========== STATS SECTION ========== */}
      <section className="bg-primary text-primary-foreground py-xl">
        <div className="max-w-7xl mx-auto px-md md:px-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-lg text-center">
            {[
              { number: '10,000+', label: 'Events Planned' },
              { number: '1,000+', label: 'Verified Vendors' },
              { number: '50,000+', label: 'Happy Users' },
              { number: '4.8★', label: 'Average Rating' },
            ].map((stat, idx) => (
              <div key={idx}>
                <p className="text-h3 font-bold mb-sm">{stat.number}</p>
                <p className="text-body-md opacity-90">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== NEWSLETTER SECTION ========== */}
      <section className="max-w-7xl mx-auto px-md md:px-lg py-xl">
        <Card className="bg-gradient-to-r from-primary/10 to-accent/10 border-primary/20 overflow-hidden">
          <CardContent className="p-lg md:p-xl space-y-md">
            <div className="space-y-sm">
              <h3 className="text-h4 font-heading">Get Exclusive Deals</h3>
              <p className="text-body-md text-muted-foreground max-w-2xl">
                Subscribe to get early access to new vendors, exclusive discounts, and planning tips.
              </p>
            </div>

            <form onSubmit={(e) => {
              e.preventDefault();
              // Handle newsletter signup
            }} className="flex gap-2 max-w-lg">
              <Input
                type="email"
                placeholder="Enter your email"
                className="h-11 flex-1"
              />
              <Button variant="primary" size="lg">
                Subscribe
              </Button>
            </form>

            <p className="text-tiny text-muted-foreground">
              We respect your privacy. Unsubscribe at any time.
            </p>
          </CardContent>
        </Card>
      </section>

      {/* ========== CTA SECTION ========== */}
      <section className="bg-accent text-accent-foreground py-jumbo">
        <div className="max-w-7xl mx-auto px-md md:px-lg text-center space-y-lg">
          <h2 className="text-h2 font-heading">Ready to Plan Your Event?</h2>
          <p className="text-body-lg max-w-2xl mx-auto opacity-90">
            Start your journey to your perfect event. Browse vendors, get quotes, and book with confidence.
          </p>
          <div className="flex flex-col sm:flex-row gap-md justify-center">
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate('/vendors')}
              className="min-w-[200px]"
            >
              Browse Vendors
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="min-w-[200px] bg-transparent border-2 border-current"
              onClick={() => navigate('/create-event')}
            >
              Plan Event
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
