import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { vendors as vendorsApi } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { ArrowLeft, Star, MapPin, Check, X, Plus, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import '../styles/VendorComparison.css';

const VendorComparison = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const vendorIds = searchParams.get('ids')?.split(',') || [];

  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [comparisonMetrics, setComparisonMetrics] = useState([
    { label: 'Rating', key: 'rating' },
    { label: 'Reviews', key: 'total_reviews' },
    { label: 'Min Price', key: 'price_min' },
    { label: 'Max Price', key: 'price_max' },
    { label: 'Experience', key: 'years_of_experience', unit: 'years' },
    { label: 'Verified', key: 'is_verified', type: 'boolean' },
    { label: 'Featured', key: 'is_featured', type: 'boolean' },
  ]);

  useEffect(() => {
    loadVendors();
  }, [vendorIds]);

  const loadVendors = async () => {
    setLoading(true);
    try {
      const vendorPromises = vendorIds.map(id => vendorsApi.getById(id));
      const results = await Promise.all(vendorPromises);
      setVendors(results.map(r => r.data).filter(v => v));
    } catch (error) {
      console.error('Failed to load vendors:', error);
      toast.error('Failed to load vendors for comparison');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToComparison = () => {
    navigate('/vendors');
  };

  const handleSelectVendor = (vendorId) => {
    navigate(`/vendors/${vendorId}`);
  };

  const handleBookSelected = (vendorId) => {
    navigate(`/booking/${vendorId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-stone-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-stone-600">Loading vendors...</p>
        </div>
      </div>
    );
  }

  if (vendors.length === 0) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-stone-900 mb-4">No vendors to compare</h2>
          <p className="text-stone-600 mb-8">Select vendors from the vendors page to compare them side by side.</p>
          <Button onClick={() => navigate('/vendors')} className="bg-primary hover:bg-primary/90">
            Browse Vendors
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-stone-50 to-white">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-6 text-stone-600 hover:text-stone-900"
          >
            <ArrowLeft size={18} className="mr-2" /> Back
          </Button>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-stone-900 mb-2">Vendor Comparison</h1>
              <p className="text-stone-600">Compare {vendors.length} {vendors.length === 1 ? 'vendor' : 'vendors'} side by side</p>
            </div>
            {vendors.length < 4 && (
              <Button
                onClick={handleAddToComparison}
                className="bg-primary hover:bg-primary/90"
              >
                <Plus size={18} className="mr-2" /> Add Vendor
              </Button>
            )}
          </div>
        </div>

        {/* Desktop Comparison Table */}
        <div className="hidden md:block overflow-x-auto rounded-2xl border border-stone-200 bg-white shadow-lg">
          <table className="w-full">
            <thead>
              <tr className="border-b border-stone-200 bg-gradient-to-r from-stone-50 to-white">
                <th className="px-6 py-4 text-left font-semibold text-stone-900 sticky left-0 bg-white">Metric</th>
                {vendors.map((vendor) => (
                  <th key={vendor.id} className="px-6 py-4 text-center min-w-[200px]">
                    <div
                      className="cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={() => handleSelectVendor(vendor.id)}
                    >
                      <h3 className="font-semibold text-stone-900 line-clamp-2 mb-2">
                        {vendor.business_name}
                      </h3>
                      <div className="flex items-center justify-center gap-1 text-sm text-stone-600">
                        {vendor.location && (
                          <>
                            <MapPin size={14} />
                            <span>{vendor.location}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Vendor Card Preview Row */}
              <tr className="border-b border-stone-200">
                <td className="px-6 py-4 font-medium text-stone-900">Quick View</td>
                {vendors.map((vendor) => (
                  <td key={vendor.id} className="px-6 py-4 text-center">
                    <div className="space-y-3">
                      <div className="flex items-center justify-center gap-1">
                        <Star size={18} className="text-amber-400 fill-amber-400" />
                        <span className="font-semibold">{vendor.rating?.toFixed(1) || 'N/A'}</span>
                        <span className="text-sm text-stone-500">
                          ({vendor.total_reviews || 0})
                        </span>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSelectVendor(vendor.id)}
                        className="w-full text-xs"
                      >
                        View Details
                      </Button>
                    </div>
                  </td>
                ))}
              </tr>

              {/* Comparison Metrics */}
              {comparisonMetrics.map((metric) => (
                <tr key={metric.key} className="border-b border-stone-200 hover:bg-stone-50/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-stone-900 sticky left-0 bg-white">
                    {metric.label}
                  </td>
                  {vendors.map((vendor) => {
                    const value = vendor[metric.key];
                    return (
                      <td key={vendor.id} className="px-6 py-4 text-center">
                        {metric.type === 'boolean' ? (
                          value ? (
                            <div className="flex items-center justify-center gap-2 text-green-600">
                              <Check size={18} />
                              <span className="text-sm">Yes</span>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center gap-2 text-stone-400">
                              <X size={18} />
                              <span className="text-sm">No</span>
                            </div>
                          )
                        ) : (
                          <span className="font-medium text-stone-900">
                            {metric.key === 'price_min' || metric.key === 'price_max'
                              ? `₹${value?.toLocaleString() || '—'}`
                              : `${value || '—'} ${metric.unit || ''}`}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}

              {/* Action Row */}
              <tr className="bg-gradient-to-r from-primary/5 to-transparent">
                <td className="px-6 py-4 font-medium text-stone-900">Action</td>
                {vendors.map((vendor) => (
                  <td key={vendor.id} className="px-6 py-4 text-center">
                    <Button
                      onClick={() => handleBookSelected(vendor.id)}
                      className="w-full bg-primary hover:bg-primary/90 text-white"
                    >
                      Book Now <ArrowRight size={16} className="ml-2" />
                    </Button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Mobile Card View */}
        <div className="md:hidden space-y-6">
          {vendors.map((vendor) => (
            <Card key={vendor.id} className="border-stone-200 overflow-hidden hover:shadow-lg transition-shadow">
              <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-6 border-b border-stone-200">
                <h3 className="text-xl font-semibold text-stone-900 mb-2">{vendor.business_name}</h3>
                {vendor.location && (
                  <div className="flex items-center gap-2 text-stone-600">
                    <MapPin size={16} />
                    <span>{vendor.location}</span>
                  </div>
                )}
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-stone-600 mb-1">Rating</p>
                    <p className="text-lg font-semibold flex items-center gap-1">
                      <Star size={16} className="text-amber-400 fill-amber-400" />
                      {vendor.rating?.toFixed(1) || 'N/A'}
                    </p>
                    <p className="text-xs text-stone-500">({vendor.total_reviews || 0} reviews)</p>
                  </div>
                  <div>
                    <p className="text-sm text-stone-600 mb-1">Experience</p>
                    <p className="text-lg font-semibold">
                      {vendor.years_of_experience || '—'} years
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-stone-600 mb-1">Min Price</p>
                    <p className="text-lg font-semibold">₹{vendor.price_min?.toLocaleString() || '—'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-stone-600 mb-1">Max Price</p>
                    <p className="text-lg font-semibold">₹{vendor.price_max?.toLocaleString() || '—'}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Button
                    variant="outline"
                    onClick={() => handleSelectVendor(vendor.id)}
                    className="w-full"
                  >
                    View Details
                  </Button>
                  <Button
                    onClick={() => handleBookSelected(vendor.id)}
                    className="w-full bg-primary hover:bg-primary/90 text-white"
                  >
                    Book Now
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Tips Section */}
        <div className="mt-16 p-8 bg-gradient-to-r from-primary/10 to-pink-500/10 rounded-2xl border border-primary/20">
          <h3 className="text-lg font-semibold text-stone-900 mb-4">Comparison Tips</h3>
          <ul className="space-y-2 text-stone-700">
            <li className="flex items-start gap-3">
              <Check size={18} className="text-primary mt-1 flex-shrink-0" />
              <span>Check ratings and reviews to understand past customer satisfaction</span>
            </li>
            <li className="flex items-start gap-3">
              <Check size={18} className="text-primary mt-1 flex-shrink-0" />
              <span>Compare price ranges to find the best value for your budget</span>
            </li>
            <li className="flex items-start gap-3">
              <Check size={18} className="text-primary mt-1 flex-shrink-0" />
              <span>Look for verified and featured vendors for added peace of mind</span>
            </li>
            <li className="flex items-start gap-3">
              <Check size={18} className="text-primary mt-1 flex-shrink-0" />
              <span>Click "View Details" to see portfolios, packages, and availability</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default VendorComparison;
