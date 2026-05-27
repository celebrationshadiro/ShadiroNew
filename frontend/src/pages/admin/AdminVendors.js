import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import CategoryBadge from '../../components/CategoryBadge';
import ProfileCompletionRing from '../../components/ProfileCompletionRing';
import { admin } from '../../lib/api';
import { Check, X, Pause, Star, Loader2, Eye, TrendingUp, Shield, Sparkles, Package } from 'lucide-react';
import { toast } from 'sonner';

const statusColors = {
  pending: 'bg-amber-100 text-amber-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  suspended: 'bg-stone-100 text-stone-800',
};

const typeFromVendor = (v) => {
  const slug = (v.category_slug || v.category_id || '').replace('cat-', '').toLowerCase();
  const vt = (v.vendor_type || '').toLowerCase();
  if (vt.includes('product') || slug === 'grocery') return 'grocery';
  return 'service';
};

const categoryKey = (v) => (v.category_slug || v.category_id || '').replace('cat-', '').toLowerCase();

const completionValue = (v) => {
  if (v.onboarding_status === 'complete') return 100;
  const missing = v.onboarding_missing_required?.length || 0;
  return Math.max(20, 100 - missing * 12);
};

const extractPayload = (response) => response?.data?.data ?? response?.data ?? response;
const extractList = (response) => {
  const payload = extractPayload(response);
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.vendors)) return payload.vendors;
  return [];
};

const VendorRow = ({
  vendor,
  onStats,
  onFeatured,
  actioning,
  onAction,
  onSelect,
}) => {
  const type = typeFromVendor(vendor);
  const category = categoryKey(vendor);
  const completion = completionValue(vendor);
  const verified = vendor.is_verified || vendor.verification_status === 'approved';
  const plan = (vendor.subscription_plan || 'free').toUpperCase();

  return (
    <Card className="p-4 hover:shadow-md transition-shadow border">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex-1 min-w-[260px]" onClick={() => onSelect(vendor)}>
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <h3 className="font-semibold text-lg">{vendor.business_name}</h3>
            <CategoryBadge slug={category} />
            <Badge className="bg-stone-100 text-stone-700">{type === 'grocery' ? 'Grocery' : 'Service'}</Badge>
            <Badge className={statusColors[vendor.status] || 'bg-stone-100'}>{vendor.status || 'approved'}</Badge>
            {verified && <Shield className="w-4 h-4 text-emerald-600" />}
            {vendor.is_featured && <Star className="w-4 h-4 text-amber-500 fill-amber-500" />}
            <Badge className="bg-primary/10 text-primary border-primary/20">Plan: {plan}</Badge>
          </div>
          <p className="text-sm text-stone-600 mb-2">
            {vendor.owner_name} • {vendor.city} • ★ {vendor.rating?.toFixed(1) || '0'} ({vendor.total_reviews || 0} reviews)
          </p>
          <div className="flex items-center gap-3 mb-2">
            <ProfileCompletionRing value={completion} />
            <div className="text-xs text-stone-500">
              Onboarding: {vendor.onboarding_status || 'unknown'}
              {vendor.onboarding_missing_required?.length ? ` • Missing ${vendor.onboarding_missing_required.length}` : ''}
            </div>
          </div>
          {vendor.description && (
            <p className="text-sm text-stone-500 mb-2 line-clamp-2">
              {vendor.description}
            </p>
          )}
        </div>

        <div className="flex flex-col items-end gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onStats(vendor)}
            className="whitespace-nowrap"
          >
            <TrendingUp className="w-4 h-4 mr-1" /> Stats
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onSelect(vendor)}
            className="whitespace-nowrap"
          >
            <Eye className="w-4 h-4 mr-1" /> Details
          </Button>

          {vendor.status === 'pending' && (
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="outline"
                onClick={() => onAction(vendor.id, 'approve')}
                disabled={actioning === vendor.id}
                className="border-green-200 text-green-600 hover:bg-green-50"
              >
                {actioning === vendor.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onAction(vendor.id, 'reject')}
                className="border-red-200 text-red-600 hover:bg-red-50"
              >
                <X className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onAction(vendor.id, 'request_changes')}
                className="border-amber-200 text-amber-700 hover:bg-amber-50"
              >
                <Eye className="w-4 h-4" />
              </Button>
            </div>
          )}

          {vendor.status === 'approved' && (
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="outline"
                onClick={() => onFeatured(vendor.id, vendor.is_featured)}
                disabled={actioning === vendor.id}
                className={vendor.is_featured ? 'border-amber-200' : ''}
              >
                <Star className={`w-4 h-4 ${vendor.is_featured ? 'fill-amber-500 text-amber-500' : ''}`} />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onAction(vendor.id, 'suspend')}
                className="border-orange-200 text-orange-600 hover:bg-orange-50"
              >
                <Pause className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onAction(vendor.id, 'request_changes')}
                className="border-amber-200 text-amber-700 hover:bg-amber-50"
              >
                <Eye className="w-4 h-4" />
              </Button>
            </div>
          )}

          {vendor.status === 'suspended' && (
            <Button size="sm" onClick={() => onAction(vendor.id, 'approve')} disabled={actioning === vendor.id}>
              {actioning === vendor.id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Reactivate'}
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

const AdminVendors = () => {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [planFilter, setPlanFilter] = useState('all');
  const [actioningId, setActioningId] = useState(null);
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [vendorStats, setVendorStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const loadVendors = useCallback(async () => {
    setLoading(true);
    try {
      const res = await admin.getVendors({});
      setVendors(extractList(res));
    } catch (err) {
      console.error('Failed to load vendors:', err);
      toast.error('Failed to load vendors');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadVendors();
  }, [loadVendors]);

  const filteredVendors = useMemo(() => {
    return (Array.isArray(vendors) ? vendors : []).filter((v) => {
      const type = typeFromVendor(v);
      const cat = categoryKey(v);
      const plan = (v.subscription_plan || 'free').toLowerCase();
      const status = (v.status || '').toLowerCase();
      if (typeFilter !== 'all' && type !== typeFilter) return false;
      if (categoryFilter !== 'all' && cat !== categoryFilter) return false;
      if (statusFilter === 'incomplete' && v.onboarding_status === 'complete') return false;
      if (statusFilter !== 'all' && statusFilter !== 'incomplete' && status !== statusFilter) return false;
      if (planFilter !== 'all' && plan !== planFilter) return false;
      return true;
    });
  }, [vendors, typeFilter, categoryFilter, statusFilter, planFilter]);

  const handleLoadStats = async (vendor) => {
    setSelectedVendor(vendor);
    setStatsLoading(true);
    try {
      const res = await admin.getVendorStats(vendor.id);
      setVendorStats(extractPayload(res));
    } catch (err) {
      toast.error('Failed to load vendor statistics');
    } finally {
      setStatsLoading(false);
    }
  };

  const handleAction = async (vendorId, action) => {
    setActioningId(vendorId);
    try {
      await admin.approveVendor(vendorId, { action });
      toast.success('Action completed');
      loadVendors();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed');
    } finally {
      setActioningId(null);
    }
  };

  const handleFeatured = async (vendorId, current) => {
    setActioningId(vendorId);
    try {
      await admin.toggleFeatured(vendorId, !current);
      toast.success(current ? 'Removed from featured' : 'Added to featured');
      loadVendors();
    } catch (err) {
      toast.error('Failed to update featured status');
    } finally {
      setActioningId(null);
    }
  };

  const DetailPanel = ({ vendor }) => {
    if (!vendor) return null;
    const type = typeFromVendor(vendor);
    const cat = categoryKey(vendor);

    const renderCategoryDetails = () => {
      if (type === 'grocery') {
        const products = vendor.grocery_items || [];
        const lowStock = products.filter((p) => (p.stock_qty ?? 0) < 5).length;
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Card className="p-4">
              <p className="text-sm text-stone-500">Products</p>
              <p className="text-xl font-semibold">{products.length}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-stone-500">Low stock alerts</p>
              <p className="text-xl font-semibold">{lowStock}</p>
            </Card>
          </div>
        );
      }

      switch (cat) {
        case 'venue':
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Card className="p-4"><p className="text-sm text-stone-500">Capacity</p><p className="text-lg font-semibold">{vendor.capacity_min || vendor.details?.capacity_min || '—'} - {vendor.capacity_max || vendor.details?.capacity_max || '—'}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Halls/Rooms</p><p className="text-lg font-semibold">{vendor.details?.halls?.length || vendor.details?.rooms?.length || '—'}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Parking</p><p className="text-lg font-semibold">{vendor.details?.parking || 'Not set'}</p></Card>
            </div>
          );
        case 'caterer':
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Card className="p-4"><p className="text-sm text-stone-500">Menu items</p><p className="text-lg font-semibold">{(vendor.caterer_menu_items || []).length}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Cuisine types</p><p className="text-lg font-semibold">{(vendor.cuisine_specializations || []).length || '—'}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Per plate</p><p className="text-lg font-semibold">₹{vendor.caterer_price_per_plate || '—'}</p></Card>
            </div>
          );
        case 'dj':
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Card className="p-4"><p className="text-sm text-stone-500">Equipment</p><p className="text-lg font-semibold">{(vendor.dj_equipment || []).length}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Team size</p><p className="text-lg font-semibold">{vendor.dj_crew_size || '—'}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Setup time</p><p className="text-lg font-semibold">{vendor.details?.dj_setup_time || '—'}</p></Card>
            </div>
          );
        case 'photographer':
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Card className="p-4"><p className="text-sm text-stone-500">Packages</p><p className="text-lg font-semibold">{(vendor.photo_packages || []).length}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Deliverables</p><p className="text-lg font-semibold">{(vendor.photo_services || []).length || '—'}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Delivery timeline</p><p className="text-lg font-semibold">{vendor.delivery_timeline || vendor.details?.delivery_timeline || '—'}</p></Card>
            </div>
          );
        case 'decor':
        case 'decorator':
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Card className="p-4"><p className="text-sm text-stone-500">Themes</p><p className="text-lg font-semibold">{(vendor.decorator_themes || []).length}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Inventory</p><p className="text-lg font-semibold">{(vendor.decorator_inventory || []).length}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Setup types</p><p className="text-lg font-semibold">{(vendor.decorator_setup_types || []).length}</p></Card>
            </div>
          );
        case 'mehandi':
          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Card className="p-4"><p className="text-sm text-stone-500">Styles</p><p className="text-lg font-semibold">{(vendor.design_styles || []).length || '—'}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Services</p><p className="text-lg font-semibold">{(vendor.mehandi_services || []).length}</p></Card>
              <Card className="p-4"><p className="text-sm text-stone-500">Home service</p><p className="text-lg font-semibold">{(vendor.home_service ?? vendor.details?.home_service) ? 'Yes' : 'No'}</p></Card>
            </div>
          );
        default:
          return (
            <div className="text-sm text-stone-500">No category details available.</div>
          );
      }
    };

    return (
      <Card className="p-5 border border-stone-200 bg-white">
        <div className="flex items-center gap-2 mb-3">
          <Package className="w-4 h-4 text-stone-500" />
          <p className="text-sm font-semibold text-stone-800">Category details</p>
        </div>
        {renderCategoryDetails()}
        {vendor.onboarding_missing_required?.length > 0 && (
          <div className="mt-4 text-sm text-stone-600">
            Missing required fields: {vendor.onboarding_missing_required.slice(0, 4).join(', ')}
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Vendor Management</h1>

      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        {['all', 'grocery', 'service'].map((v) => (
          <Button key={v} variant={typeFilter === v ? 'default' : 'outline'} size="sm" onClick={() => setTypeFilter(v)} className="whitespace-nowrap">
            {v === 'all' ? 'All Types' : v.charAt(0).toUpperCase() + v.slice(1)}
          </Button>
        ))}
        {['all', 'venue', 'dj', 'caterer', 'photographer', 'decorator', 'mehandi'].map((c) => (
          <Button key={c} variant={categoryFilter === c ? 'default' : 'outline'} size="sm" onClick={() => setCategoryFilter(c)} className="whitespace-nowrap">
            {c === 'all' ? 'All Categories' : c.charAt(0).toUpperCase() + c.slice(1)}
          </Button>
        ))}
      </div>
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {['all', 'pending', 'approved', 'incomplete', 'suspended', 'rejected'].map((s) => (
          <Button key={s} variant={statusFilter === s ? 'default' : 'outline'} size="sm" onClick={() => setStatusFilter(s)} className="whitespace-nowrap">
            {s === 'all' ? 'All Status' : s.charAt(0).toUpperCase() + s.slice(1)}
          </Button>
        ))}
        {['all', 'free', 'pro', 'enterprise'].map((p) => (
          <Button key={p} variant={planFilter === p ? 'default' : 'outline'} size="sm" onClick={() => setPlanFilter(p)} className="whitespace-nowrap">
            {p === 'all' ? 'All Plans' : p.charAt(0).toUpperCase() + p.slice(1)}
          </Button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="h-32 bg-white border border-stone-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : filteredVendors.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-stone-500">No vendors match current filters.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredVendors.map((v) => (
            <VendorRow
              key={v.id}
              vendor={v}
              onStats={handleLoadStats}
              onFeatured={handleFeatured}
              actioning={actioningId}
              onAction={handleAction}
              onSelect={setSelectedVendor}
            />
          ))}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {selectedVendor && <DetailPanel vendor={selectedVendor} />}
        {selectedVendor && (
          <Card className="p-5 border border-stone-200 bg-white">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-stone-500" />
              <p className="text-sm font-semibold text-stone-800">Performance</p>
            </div>
            {statsLoading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm text-stone-500">Loading stats...</span>
              </div>
            ) : vendorStats ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <Card className="p-3 bg-blue-50 border-none">
                  <p className="text-xs text-blue-700">Bookings</p>
                  <p className="text-lg font-semibold text-blue-900">{vendorStats.total_bookings}</p>
                </Card>
                <Card className="p-3 bg-green-50 border-none">
                  <p className="text-xs text-green-700">Confirmed</p>
                  <p className="text-lg font-semibold text-green-900">{vendorStats.confirmed_bookings}</p>
                </Card>
                <Card className="p-3 bg-purple-50 border-none">
                  <p className="text-xs text-purple-700">Revenue</p>
                  <p className="text-lg font-semibold text-purple-900">₹{(vendorStats.total_revenue || 0).toLocaleString()}</p>
                </Card>
                <Card className="p-3 bg-yellow-50 border-none">
                  <p className="text-xs text-yellow-700">Rating</p>
                  <p className="text-lg font-semibold text-yellow-900">★ {vendorStats.average_rating}</p>
                </Card>
                <Card className="p-3 bg-rose-50 border-none">
                  <p className="text-xs text-rose-700">Emergency Cancels</p>
                  <p className="text-lg font-semibold text-rose-900">{vendorStats.emergency_count || 0}</p>
                </Card>
                <Card className="p-3 bg-stone-50 border-none">
                  <p className="text-xs text-stone-700">Acceptance Rate</p>
                  <p className="text-lg font-semibold text-stone-900">{Math.round((vendorStats.acceptance_rate || 0) * 100)}%</p>
                </Card>
              </div>
            ) : (
              <p className="text-sm text-stone-500">Select a vendor to view stats.</p>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default AdminVendors;
