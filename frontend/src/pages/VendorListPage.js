import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useLocation, Link } from 'react-router-dom';
import { vendors as vendorsApi, categories } from '../lib/api';
import { FALLBACK_CATEGORIES } from '../lib/fallbackCategories';
import { Star, MapPin, DollarSign, Filter } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

const VendorListPage = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [vendorList, setVendorList] = useState([]);
  const [categoryList, setCategoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category_id: searchParams.get('category_id') || 'all',
    city: searchParams.get('city') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    search: searchParams.get('search') || '',
  });
  const [sortBy, setSortBy] = useState('nearest');

  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      category_id: searchParams.get('category_id') || location.state?.category || 'all',
      city: searchParams.get('city') || prev.city || '',
      min_price: searchParams.get('min_price') || prev.min_price || '',
      max_price: searchParams.get('max_price') || prev.max_price || '',
      search: searchParams.get('search') || location.state?.search || '',
    }));
  }, [searchParams, location.state]);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await categories.getAll();
      const data = response?.data;
      setCategoryList(Array.isArray(data) && data.length > 0 ? data : FALLBACK_CATEGORIES);
    } catch (error) {
      console.error('Failed to load categories:', error);
      setCategoryList(FALLBACK_CATEGORIES);
    }
  };

  const loadVendors = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      Object.keys(filters).forEach((key) => {
        const val = filters[key];
        if (val && val !== 'all') params[key] = val;
      });
      const response = await vendorsApi.getAll(params);
      // Handle { data: { items: [...], total, ... } } response structure
      const data = response?.data;
      let vendors = [];
      if (data?.items && Array.isArray(data.items)) {
        vendors = data.items;
      } else if (Array.isArray(data)) {
        vendors = data;
      } else if (Array.isArray(response)) {
        vendors = response;
      }
      setVendorList(vendors);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadVendors();
  }, [loadVendors]);

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  const applyFilters = () => {
    loadVendors();
  };

  const getAvailabilityBadge = (vendor) => {
    if (vendor.is_available === false) {
      return { label: 'Unavailable', className: 'bg-red-50 text-red-700' };
    }
    if (vendor.next_available_date) {
      return { label: `Next: ${new Date(vendor.next_available_date).toLocaleDateString()}`, className: 'bg-amber-50 text-amber-800' };
    }
    return { label: 'Available', className: 'bg-emerald-50 text-emerald-700' };
  };

  const getSuggestions = (vendor) => {
    const suggestions = [];
    const min = parseFloat(filters.min_price || 0);
    const max = parseFloat(filters.max_price || 0);
    if ((min || max) && vendor.base_price) {
      if ((!min || vendor.base_price >= min) && (!max || vendor.base_price <= max)) {
        suggestions.push('Best for your budget');
      }
    }
    if (vendor.total_reviews >= 50 && vendor.rating >= 4.5) {
      suggestions.push('Frequently booked for weddings');
    }
    return suggestions.slice(0, 2);
  };

  const scoreNearest = (vendor) => {
    const city = (filters.city || '').toLowerCase();
    if (!city) return 0;
    const vendorCity = (vendor.city || vendor.location || '').toLowerCase();
    if (vendorCity.includes(city)) return 2;
    const areas = Array.isArray(vendor.service_areas) ? vendor.service_areas.join(' ').toLowerCase() : '';
    return areas.includes(city) ? 1 : 0;
  };

  const sortedVendors = [...vendorList].sort((a, b) => {
    if (sortBy === 'rating') return (b.rating || 0) - (a.rating || 0);
    if (sortBy === 'availability') return (b.is_available === false ? 0 : 1) - (a.is_available === false ? 0 : 1);
    if (sortBy === 'nearest') return scoreNearest(b) - scoreNearest(a);
    return 0;
  });

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-7xl mx-auto w-full px-4 md:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight mb-4 font-heading">
            Find Your Perfect Vendor
          </h1>
          <p className="text-lg text-stone-600">Browse verified professionals for your event</p>
        </div>

        {/* Filters */}
        <Card className="p-6 mb-8 bg-white rounded-2xl border border-stone-100" data-testid="filter-card">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <div>
              <Select
                value={filters.category_id}
                onValueChange={(value) => handleFilterChange('category_id', value)}
              >
                <SelectTrigger className="h-12 rounded-lg" data-testid="category-filter">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categoryList.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Input
              placeholder="City"
              className="h-12 rounded-lg"
              value={filters.city}
              onChange={(e) => handleFilterChange('city', e.target.value)}
              data-testid="city-filter"
            />
            <Input
              type="number"
              placeholder="Min Price"
              className="h-12 rounded-lg"
              value={filters.min_price}
              onChange={(e) => handleFilterChange('min_price', e.target.value)}
              data-testid="min-price-filter"
            />
            <Input
              type="number"
              placeholder="Max Price"
              className="h-12 rounded-lg"
              value={filters.max_price}
              onChange={(e) => handleFilterChange('max_price', e.target.value)}
              data-testid="max-price-filter"
            />
            <Select
              value={sortBy}
              onValueChange={(value) => setSortBy(value)}
            >
              <SelectTrigger className="h-12 rounded-lg">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="nearest">Nearest</SelectItem>
                <SelectItem value="rating">Rating</SelectItem>
                <SelectItem value="availability">Availability</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={applyFilters}
              className="h-12 bg-primary hover:bg-primary/90 rounded-lg"
              data-testid="apply-filters-button"
            >
              <Filter size={18} className="mr-2" /> Apply Filters
            </Button>
          </div>
        </Card>

        {/* Vendor Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array.from({ length: 6 }).map((_, idx) => (
              <Card key={idx} className="rounded-2xl overflow-hidden border border-stone-100">
                <div className="h-48 bg-stone-200 animate-pulse" />
                <div className="p-6 space-y-3">
                  <div className="h-5 bg-stone-200 rounded animate-pulse w-2/3" />
                  <div className="h-4 bg-stone-200 rounded animate-pulse w-1/2" />
                  <div className="h-4 bg-stone-200 rounded animate-pulse w-1/3" />
                </div>
              </Card>
            ))}
          </div>
        ) : vendorList.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-stone-500 text-lg">No vendors found. Try adjusting your filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" data-testid="vendor-grid">
            {sortedVendors.map((vendor) => (
              <Link key={vendor.id} to={`/vendors/${vendor.id}`} data-testid={`vendor-card-${vendor.id}`}>
                <Card className="group relative overflow-hidden rounded-2xl bg-white border border-stone-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 h-full">
                  <div className="aspect-[4/3] relative overflow-hidden">
                    {vendor.media && vendor.media.length > 0 ? (
                      <img
                        src={vendor.media[0].url}
                        alt={vendor.business_name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full bg-stone-200 flex items-center justify-center">
                        <span className="text-stone-400 text-4xl font-heading">{vendor.business_name[0]}</span>
                      </div>
                    )}
                    {vendor.is_verified && (
                      <div className="absolute top-4 right-4 bg-secondary text-white px-3 py-1 rounded-full text-sm font-medium">
                        Verified
                      </div>
                    )}
                    <div className="absolute bottom-3 left-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getAvailabilityBadge(vendor).className}`}>
                        {getAvailabilityBadge(vendor).label}
                      </span>
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="text-2xl font-medium mb-2">{vendor.business_name}</h3>
                    {vendor.location && (
                      <div className="flex items-center text-stone-600 mb-2">
                        <MapPin size={16} className="mr-1" />
                        <span className="text-sm">{vendor.location}</span>
                      </div>
                    )}
                    {getSuggestions(vendor).length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-2">
                        {getSuggestions(vendor).map((s, idx) => (
                          <span key={idx} className="text-xs px-2 py-1 rounded-full bg-stone-100 text-stone-700">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Star size={16} className="text-secondary fill-secondary mr-1" />
                        <span className="font-medium">{vendor.rating.toFixed(1)}</span>
                        <span className="text-stone-500 text-sm ml-1">({vendor.total_reviews})</span>
                      </div>
                      {vendor.base_price && (
                        <div className="flex items-center text-primary font-medium">
                          <DollarSign size={16} />
                          <span>₹{vendor.base_price.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default VendorListPage;
