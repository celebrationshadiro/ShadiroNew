import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { categories, recommendationsApi } from '../lib/api';
import { FALLBACK_CATEGORIES } from '../lib/fallbackCategories';
import { Search, ArrowRight, Star, Shield, Sparkles, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { toast } from 'sonner';

const HomePage = () => {
  const { user } = useAuth();
  const [categoryList, setCategoryList] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [budgetRange, setBudgetRange] = useState({ min: '', max: '' });

  useEffect(() => {
    loadCategories();
    if (user) {
      loadRecommendations();
    }
  }, [user]);

  const loadCategories = async () => {
    setCategoriesLoading(true);
    try {
      const response = await categories.getAll();
      const data = response?.data;
      setCategoryList(Array.isArray(data) && data.length > 0 ? data : FALLBACK_CATEGORIES);
    } catch (error) {
      console.error('Failed to load categories:', error);
      setCategoryList(FALLBACK_CATEGORIES);
    } finally {
      setCategoriesLoading(false);
    }
  };

  const loadRecommendations = async () => {
    setRecommendationsLoading(true);
    try {
      const response = await recommendationsApi.getPersonalizedRecommendations(5);
      const data = response?.data;
      if (Array.isArray(data)) {
        setRecommendations(data);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setRecommendationsLoading(false);
    }
  };

  const displayCategories = categoryList.length > 0 ? categoryList : FALLBACK_CATEGORIES;

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (searchQuery) params.append('search', searchQuery);
    if (budgetRange.min) params.append('min_price', budgetRange.min);
    if (budgetRange.max) params.append('max_price', budgetRange.max);
    window.location.href = `/vendors?${params.toString()}`;
  };

  return (
    <div className="min-h-screen bg-neutral-50 overflow-hidden">
      {/* Hero - modern gradient + image overlay */}
      <section className="relative min-h-[85vh] flex items-center">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1519741497674-611481863552?w=1920&q=80')`,
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
        <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-transparent to-transparent" />

        <div className="relative max-w-6xl mx-auto w-full px-4 md:px-8 py-24 z-10">
          <div className="max-w-2xl">
            <p className="text-primary/90 font-medium tracking-widest uppercase text-sm mb-4">
              India&apos;s trusted event marketplace
            </p>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6 leading-[1.1]">
              Plan your dream{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-pink-400">
                celebration
              </span>
            </h1>
            <p className="text-lg md:text-xl text-white/80 mb-10 leading-relaxed max-w-xl">
              Connect with 500+ verified vendors. Get custom quotes. Book with confidence.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
              <Link to="/grocery/cart" className="block">
                <div className="group rounded-2xl bg-white/10 border border-white/20 px-4 py-4 flex items-center justify-between backdrop-blur hover:bg-white/20 transition">
                  <div>
                    <p className="text-sm text-white/80">Groceries · Delivery</p>
                    <p className="text-lg font-semibold text-white">Shop Groceries</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-white group-hover:translate-x-1 transition" />
                </div>
              </Link>
              <Link to="/vendors" className="block">
                <div className="group rounded-2xl bg-white px-4 py-4 flex items-center justify-between shadow-lg shadow-black/10 hover:-translate-y-0.5 transition">
                  <div>
                    <p className="text-sm text-stone-500">Services · Events</p>
                    <p className="text-lg font-semibold text-stone-900">Book Event Services</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-stone-900 group-hover:translate-x-1 transition" />
                </div>
              </Link>
              <Link to="/plan-my-event" className="block">
                <div className="group rounded-2xl bg-primary/10 border border-white/20 px-4 py-4 flex items-center justify-between backdrop-blur hover:bg-primary/20 transition">
                  <div>
                    <p className="text-sm text-white/80">Concierge</p>
                    <p className="text-lg font-semibold text-white">Plan my event for me</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-white group-hover:translate-x-1 transition" />
                </div>
              </Link>
            </div>

            {/* Search Card - glassmorphism */}
            <Card className="bg-white/95 backdrop-blur-xl border-0 shadow-2xl p-6 md:p-8 rounded-3xl">
              <div className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-stone-400" size={22} />
                  <Input
                    placeholder="Venues, photographers, caterers..."
                    className="h-14 pl-14 rounded-2xl border-stone-200 text-base bg-stone-50/50 focus:bg-white"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    type="number"
                    placeholder="Min budget (₹)"
                    className="h-12 rounded-xl border-stone-200"
                    value={budgetRange.min}
                    onChange={(e) => setBudgetRange({ ...budgetRange, min: e.target.value })}
                  />
                  <Input
                    type="number"
                    placeholder="Max budget (₹)"
                    className="h-12 rounded-xl border-stone-200"
                    value={budgetRange.max}
                    onChange={(e) => setBudgetRange({ ...budgetRange, max: e.target.value })}
                  />
                </div>
                <Button
                  onClick={handleSearch}
                  className="w-full h-14 rounded-2xl text-base font-semibold bg-primary hover:bg-primary/90 shadow-lg shadow-primary/25"
                >
                  Find Vendors <ArrowRight className="ml-2" size={20} />
                </Button>
              </div>
            </Card>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-8 h-12 rounded-full border-2 border-white/50 flex justify-center pt-2">
            <div className="w-1.5 h-2 rounded-full bg-white/80" />
          </div>
        </div>
      </section>

      {/* Categories - modern card grid */}
      <section className="relative py-24 md:py-32 bg-white">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-stone-200 to-transparent" />
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-16">
            <p className="text-primary font-semibold text-sm tracking-wider uppercase mb-3">Browse by category</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-stone-900 mb-4">
              Find your perfect vendor
            </h2>
            <p className="text-stone-500 text-lg max-w-2xl mx-auto">
              From venues to photography, catering to entertainment — everything for your special day
            </p>
          </div>

          {categoriesLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="aspect-[4/3] rounded-2xl bg-stone-100 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6" data-testid="category-grid">
              {displayCategories.map((category, index) => (
                <Link
                  key={category.id}
                  to={`/vendors?category_id=${category.id}`}
                  className="group block"
                  data-testid={`category-card-${category.slug}`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="relative overflow-hidden rounded-2xl aspect-[4/3] bg-stone-100 shadow-sm group-hover:shadow-xl transition-all duration-500 ease-out">
                    <img
                      src={category.image_url}
                      alt={category.name}
                      className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-90 group-hover:opacity-95 transition-opacity" />
                    <div className="absolute inset-0 p-5 flex flex-col justify-end">
                      <h3 className="text-lg font-semibold text-white mb-1 group-hover:translate-y-0 translate-y-0">
                        {category.name}
                      </h3>
                      <p className="text-white/80 text-sm line-clamp-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        {category.description}
                      </p>
                      <span className="inline-flex items-center mt-2 text-primary/90 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                        Explore <ArrowRight className="ml-1 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Personalized Recommendations - for logged in users */}
      {user && recommendations.length > 0 && (
        <section className="py-24 md:py-32 bg-gradient-to-b from-stone-50 to-white">
          <div className="max-w-7xl mx-auto px-4 md:px-8">
            <div className="flex items-center gap-3 mb-4">
              <Zap className="text-primary" size={24} />
              <p className="text-primary font-semibold text-sm tracking-wider uppercase">AI-Powered</p>
            </div>
            <div className="mb-16">
              <h2 className="text-4xl font-bold tracking-tight text-stone-900 mb-4">
                Recommended for you
              </h2>
              <p className="text-stone-500 text-lg max-w-2xl">
                Based on your preferences and event requirements, we&apos;ve selected these top vendors just for you.
              </p>
            </div>

            {recommendationsLoading ? (
              <div className="text-center py-12">
                <p className="text-stone-500">Loading recommendations...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                {recommendations.map((vendor) => (
                  <Link key={vendor._id} to={`/vendors/${vendor._id}`}>
                    <Card className="group h-full bg-white border border-stone-100 shadow-sm hover:shadow-lg hover:border-primary/30 transition-all duration-300 overflow-hidden rounded-2xl flex flex-col">
                      {/* Vendor Image */}
                      <div className="relative overflow-hidden flex-shrink-0 h-40 bg-stone-100">
                        {vendor.media && vendor.media.length > 0 ? (
                          <img
                            src={vendor.media[0]}
                            alt={vendor.business_name}
                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5">
                            <Sparkles className="text-primary/40" size={40} />
                          </div>
                        )}
                        {vendor.recommendation_score && (
                          <div className="absolute top-3 right-3 bg-gradient-to-r from-primary to-pink-500 text-white px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
                            <Star size={12} fill="currentColor" />
                            {vendor.recommendation_score.toFixed(0)}%
                          </div>
                        )}
                      </div>

                      {/* Vendor Info */}
                      <div className="flex-1 p-4 flex flex-col">
                        <h3 className="font-semibold text-stone-900 line-clamp-2 text-sm mb-2 group-hover:text-primary transition-colors">
                          {vendor.business_name}
                        </h3>

                        {/* Category Badge */}
                        <p className="text-xs text-primary/70 font-medium uppercase tracking-wider mb-3">
                          {vendor.category}
                        </p>

                        {/* Rating */}
                        <div className="flex items-center gap-2 mb-4">
                          <div className="flex items-center gap-0.5">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                size={14}
                                className={i < Math.floor(vendor.avg_rating || 0) ? 'fill-amber-400 text-amber-400' : 'text-stone-200'}
                              />
                            ))}
                          </div>
                          <span className="text-xs text-stone-600">
                            {vendor.review_count || 0} reviews
                          </span>
                        </div>

                        {/* Price Range */}
                        {vendor.min_price && vendor.max_price && (
                          <p className="text-xs text-stone-500 mb-3">
                            ₹{(vendor.min_price / 1000).toFixed(0)}k - ₹{(vendor.max_price / 1000).toFixed(0)}k
                          </p>
                        )}

                        {/* View Profile Button */}
                        <Button
                          size="sm"
                          className="w-full mt-auto rounded-xl bg-primary/10 text-primary hover:bg-primary hover:text-white transition-all text-sm font-medium"
                        >
                          View Profile
                        </Button>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Features - refined */}
      <section className="py-24 md:py-32 bg-stone-50">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
          <div className="text-center mb-16">
            <p className="text-primary font-semibold text-sm tracking-wider uppercase mb-3">Why Shadiro</p>
            <h2 className="text-4xl font-bold tracking-tight text-stone-900 mb-4">
              Plan with confidence
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-16">
            <div className="relative group">
              <div className="p-8 rounded-3xl bg-white border border-stone-100 shadow-sm hover:shadow-xl hover:border-primary/20 transition-all duration-300">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                  <Search className="text-primary" size={28} />
                </div>
                <h3 className="text-xl font-semibold text-stone-900 mb-3">Budget-based matching</h3>
                <p className="text-stone-500 leading-relaxed">
                  Get matched with vendors that fit your budget and requirements perfectly.
                </p>
              </div>
            </div>

            <div className="relative group">
              <div className="p-8 rounded-3xl bg-white border border-stone-100 shadow-sm hover:shadow-xl hover:border-primary/20 transition-all duration-300">
                <div className="w-14 h-14 rounded-2xl bg-amber-100 flex items-center justify-center mb-6 group-hover:bg-amber-200/80 transition-colors">
                  <Shield className="text-amber-600" size={28} />
                </div>
                <h3 className="text-xl font-semibold text-stone-900 mb-3">Verified vendors</h3>
                <p className="text-stone-500 leading-relaxed">
                  All vendors are verified and rated by real customers for your peace of mind.
                </p>
              </div>
            </div>

            <div className="relative group">
              <div className="p-8 rounded-3xl bg-white border border-stone-100 shadow-sm hover:shadow-xl hover:border-primary/20 transition-all duration-300">
                <div className="w-14 h-14 rounded-2xl bg-violet-100 flex items-center justify-center mb-6 group-hover:bg-violet-200/80 transition-colors">
                  <Sparkles className="text-violet-600" size={28} />
                </div>
                <h3 className="text-xl font-semibold text-stone-900 mb-3">Custom packages</h3>
                <p className="text-stone-500 leading-relaxed">
                  Choose from Silver, Gold, or Platinum packages or request custom quotes.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-stone-900">
        <div className="max-w-4xl mx-auto px-4 md:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to plan your event?
          </h2>
          <p className="text-stone-400 text-lg mb-10">
            Join thousands of happy couples and families who planned their dream celebration with Shadiro
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/vendors">
              <Button size="lg" className="h-14 px-10 rounded-2xl text-base font-semibold bg-primary hover:bg-primary/90">
                Browse Vendors
              </Button>
            </Link>
            <Link to="/vendor-register">
              <Button size="lg" variant="outline" className="h-14 px-10 rounded-2xl text-base font-semibold border-stone-600 text-white hover:bg-stone-800">
                Become a Vendor
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
