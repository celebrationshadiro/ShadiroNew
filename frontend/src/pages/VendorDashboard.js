import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { vendorProfile, vendorEarnings, vendorPayouts, packages as packagesApi, quotes as quotesApi, bookingsApi, vendors as vendorsApi, vendorVerificationApi, groceryApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { EmergencyCancelModal } from '../components/EmergencyCancelModal';
import AssistantWidget from '../components/assistant/AssistantWidget';
import { Store, Package, MessageSquare, Star, Plus, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { isProductVendor } from '../lib/vendorType';
import '../styles/VendorDashboard.css';

// Extracted sub-components
import GroceryVendorDashboard from '../components/vendor-dashboard/GroceryVendorDashboard';
import { VenueTab, DJTab, CatererTab, PhotographyTab, DecoratorTab, MehandiTab } from '../components/vendor-dashboard/CategoryTabs';
import BookingsTab from '../components/vendor-dashboard/BookingsTab';
import PricingRulesTab from '../components/vendor-dashboard/PricingRulesTab';
import PayoutsTab from '../components/vendor-dashboard/PayoutsTab';

const normalizeBookingStatus = (raw) => String(raw || '').toUpperCase();

const formatCurrency = (amount) => {
  const value = Number(amount || 0);
  return `₹${value.toLocaleString('en-IN')}`;
};

const StatCard = ({ icon: Icon, value, label, bgColor }) => (
  <Card className="p-6 bg-white rounded-2xl border border-stone-100">
    <div className="flex items-center gap-4">
      <div className={`w-12 h-12 ${bgColor} rounded-xl flex items-center justify-center`}>
        <Icon className={bgColor.replace('/10', '').replace('bg-', 'text-')} size={24} />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-stone-600 text-sm">{label}</p>
      </div>
    </div>
  </Card>
);

const SkeletonCard = ({ lines = 3 }) => (
  <Card className="p-5 bg-white rounded-2xl border border-stone-100 animate-pulse">
    <div className="h-4 w-24 bg-stone-200 rounded mb-3" />
    {[...Array(lines)].map((_, i) => (
      <div key={i} className={`h-3 bg-stone-200 rounded ${i === lines - 1 ? 'w-3/5' : 'w-full'} mb-2`} />
    ))}
  </Card>
);

const PackageCard = ({ pkg, onEdit }) => {
  const tierMap = { silver: 'BASIC', gold: 'STANDARD', platinum: 'PREMIUM' };
  const tierLabel = tierMap[(pkg.tier || '').toLowerCase()] || (pkg.tier || '').toUpperCase();
  return (
  <Card className="p-6 bg-white rounded-2xl border border-stone-100 hover:shadow-lg transition-all">
    <div className="text-center mb-4">
      <div className="inline-block px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium mb-3">
        {tierLabel}
      </div>
      <h3 className="text-2xl font-semibold mb-2">{pkg.name}</h3>
      <div className="text-3xl font-bold text-primary">₹{(pkg.price || 0).toLocaleString()}</div>
    </div>
    <Button onClick={() => onEdit(pkg.id)} variant="outline" className="w-full rounded-lg">
      Edit Package
    </Button>
  </Card>
  );
};

const VendorDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [vendor, setVendor] = useState(null);
  const [packages, setPackages] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [pricingRules, setPricingRules] = useState([]);
  const [pricingSaving, setPricingSaving] = useState(false);
  const [verificationUploading, setVerificationUploading] = useState(false);
  const [groceryItems, setGroceryItems] = useState([]);
  const [groceryOrders, setGroceryOrders] = useState([]);
  const [groceryLoading, setGroceryLoading] = useState(false);
  const [newItem, setNewItem] = useState({ name: '', category: '', unit: 'kg', unit_price: '', stock_qty: '' });
  const [tabValue, setTabValue] = useState('bookings');
  const [earnings, setEarnings] = useState(null);
  const [payouts, setPayouts] = useState([]);
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutSubmitting, setPayoutSubmitting] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    loadVendorDashboard();
  }, [user, navigate]);

  const loadVendorDashboard = async () => {
    setLoading(true);
    try {
      const vendorRes = await vendorProfile.getMyVendor();
      const myVendor = vendorRes.data;

      if (myVendor) {
        setVendor(myVendor);
        setPricingRules(myVendor.pricing_rules || []);
        const earningsRes = await vendorEarnings.getSummary().catch(() => null);
        if (earningsRes?.data) setEarnings(earningsRes.data);
        const payoutsRes = await vendorPayouts.list().catch(() => null);
        if (payoutsRes?.data) setPayouts(Array.isArray(payoutsRes.data) ? payoutsRes.data : []);
        if (isProductVendor(myVendor)) {
          setGroceryLoading(true);
          const [itemsRes, ordersRes] = await Promise.all([
            groceryApi.listVendorItems(myVendor.id),
            groceryApi.listOrders(),
          ]);
          setGroceryItems(itemsRes.data?.items || []);
          setGroceryOrders(ordersRes.data || []);
          setGroceryLoading(false);
          return;
        }
        const [packagesRes, quotesRes, bookingsRes] = await Promise.all([
          packagesApi.getAll({ vendor_id: myVendor.id }),
          quotesApi.getAll({ vendor_id: myVendor.id }),
          bookingsApi.getVendorBookings?.({ vendor_id: myVendor.id }) || Promise.resolve({ data: [] }),
        ]);
        setPackages(packagesRes.data);
        setQuotes(quotesRes.data);
        setBookings(bookingsRes.data || []);
      }
    } catch (error) {
      const status = error?.response?.status;
      if (status === 404) {
        setVendor(null);
        return;
      }
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptBooking = async (bookingId) => {
    try {
      await bookingsApi?.updateBookingStatus?.(bookingId, 'confirmed');
      toast.success('Booking accepted');
      loadVendorDashboard();
    } catch (error) {
      toast.error('Failed to accept booking');
    }
  };

  const handleRejectBooking = async (bookingId) => {
    try {
      await bookingsApi?.updateBookingStatus?.(bookingId, 'rejected');
      toast.success('Booking rejected');
      loadVendorDashboard();
    } catch (error) {
      toast.error('Failed to reject booking');
    }
  };

  const handleEmergencyCancel = (bookingId) => {
    const booking = bookings.find(b => (b.id || b._id) === bookingId);
    if (booking) {
      setSelectedBooking(booking);
      setShowEmergencyModal(true);
    }
  };

  const pendingBookings = useMemo(
    () =>
      (bookings || []).filter((b) => {
        const status = normalizeBookingStatus(b.status);
        return status === 'PAYMENT_RECEIVED' || status === 'PENDING_VENDOR' || status === 'PENDING';
      }),
    [bookings]
  );

  const confirmedBookings = useMemo(
    () => (bookings || []).filter((b) => normalizeBookingStatus(b.status) === 'CONFIRMED'),
    [bookings]
  );

  const handleAddPricingRule = () => {
    const nextRule = {
      id: `rule_${Date.now()}`,
      label: 'Seasonal uplift',
      start_date: '',
      end_date: '',
      days_of_week: [],
      multiplier: 1.1,
      flat_fee: 0,
    };
    setPricingRules((prev) => [...prev, nextRule]);
  };

  const handleUpdatePricingRule = (index, field, value) => {
    setPricingRules((prev) =>
      prev.map((rule, idx) => (idx === index ? { ...rule, [field]: value } : rule))
    );
  };

  const handleRemovePricingRule = (index) => {
    setPricingRules((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSavePricingRules = async () => {
    if (!vendor) return;
    setPricingSaving(true);
    try {
      const normalized = pricingRules.map((rule) => ({
        ...rule,
        days_of_week: Array.isArray(rule.days_of_week)
          ? rule.days_of_week
          : String(rule.days_of_week || '')
              .split(',')
              .map((d) => d.trim())
              .filter(Boolean),
        multiplier: rule.multiplier === '' ? null : Number(rule.multiplier),
        flat_fee: rule.flat_fee === '' ? null : Number(rule.flat_fee),
      }));
      const res = await vendorsApi.updatePricingRules(vendor.id, normalized);
      setVendor(res.data);
      setPricingRules(res.data?.pricing_rules || []);
      toast.success('Pricing rules saved');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save pricing rules');
    } finally {
      setPricingSaving(false);
    }
  };

  const handleAddGroceryItem = async () => {
    if (!vendor) return;
    if (!newItem.name || !newItem.unit_price) {
      toast.error('Please enter item name and price');
      return;
    }
    try {
      const payload = {
        vendor_id: vendor.id,
        name: newItem.name,
        category: newItem.category || null,
        unit: newItem.unit || 'kg',
        unit_price: Number(newItem.unit_price),
        stock_qty: Number(newItem.stock_qty || 0),
        is_available: true,
      };
      await groceryApi.addItem(payload);
      const res = await groceryApi.listVendorItems(vendor.id);
      setGroceryItems(res.data?.items || []);
      setNewItem({ name: '', category: '', unit: 'kg', unit_price: '', stock_qty: '' });
      toast.success('Item added');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add item');
    }
  };

  const handleUpdateStock = async (itemId, stock_qty) => {
    try {
      await groceryApi.updateItem(itemId, { stock_qty: Number(stock_qty) });
      const res = await groceryApi.listVendorItems(vendor.id);
      setGroceryItems(res.data?.items || []);
    } catch (error) {
      toast.error('Failed to update stock');
    }
  };

  const handleVerificationUpload = async (file) => {
    if (!file) return;
    setVerificationUploading(true);
    try {
      await vendorVerificationApi.uploadDocument(file);
      toast.success('Document uploaded for verification');
      loadVendorDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setVerificationUploading(false);
    }
  };

  const handleEmergendaryCancelSubmit = async (reason, notes) => {
    try {
      const bookingId = selectedBooking.id || selectedBooking._id;
      let impact_score = null;
      try {
        const amount = selectedBooking.total_amount || selectedBooking.price || 0;
        const daysOut = selectedBooking.event_date ? Math.max(0, Math.ceil((new Date(selectedBooking.event_date) - new Date()) / (1000 * 60 * 60 * 24))) : 0;
        impact_score = Math.round((amount || 0) * (daysOut <= 3 ? 1.5 : 1));
      } catch {
        impact_score = null;
      }
      await bookingsApi?.cancelBooking?.(bookingId, { 
        reason, 
        vendor_cancelled: true,
        notes,
        impact_score
      });
      toast.success('Booking cancelled. Admin will assign replacement vendor.');
      setShowEmergencyModal(false);
      setSelectedBooking(null);
      loadVendorDashboard();
    } catch (error) {
      toast.error('Failed to cancel booking');
    }
  };

  const handleRequestPayout = async () => {
    const amount = Number(payoutAmount);
    if (!amount || amount <= 0) {
      toast.error('Enter a valid payout amount');
      return;
    }
    if (earnings && amount > Number(earnings.payout_balance || 0)) {
      toast.error('Amount exceeds available payout balance');
      return;
    }
    setPayoutSubmitting(true);
    try {
      await vendorPayouts.request(amount);
      toast.success('Payout request submitted');
      setPayoutAmount('');
      const payoutsRes = await vendorPayouts.list().catch(() => null);
      if (payoutsRes?.data) setPayouts(Array.isArray(payoutsRes.data) ? payoutsRes.data : []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to request payout');
    } finally {
      setPayoutSubmitting(false);
    }
  };

  const categorySlug = useMemo(() => (vendor?.category_slug || vendor?.category_id || '').replace(/^cat-/, ''), [vendor]);
  const categoryTabValue = useMemo(() => {
    if (!vendor || isProductVendor(vendor)) return null;
    if (categorySlug.includes('venue')) return 'category-venue';
    if (categorySlug.includes('dj') || categorySlug.includes('entertainment')) return 'category-dj';
    if (categorySlug.includes('cater')) return 'category-caterer';
    if (categorySlug.includes('photo')) return 'category-photography';
    if (categorySlug.includes('decor')) return 'category-decorator';
    if (categorySlug.includes('mehandi')) return 'category-mehandi';
    return null;
  }, [categorySlug, vendor]);

  useEffect(() => {
    if (!vendor || isProductVendor(vendor)) return;
    if (categoryTabValue) {
      setTabValue(categoryTabValue);
    }
  }, [vendor, categoryTabValue]);

  // ── Loading state ───────────────────────────────────────────────
  if (loading && !vendor) {
    return (
      <div className="min-h-screen bg-stone-50">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-10 space-y-6">
          <div className="h-8 w-64 bg-stone-200 rounded animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SkeletonCard /><SkeletonCard /><SkeletonCard />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SkeletonCard lines={4} /><SkeletonCard lines={4} />
          </div>
        </div>
      </div>
    );
  }

  // ── No vendor profile ───────────────────────────────────────────
  if (!vendor) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <Card className="p-12 text-center bg-white rounded-2xl max-w-md">
          <Store className="mx-auto mb-4 text-stone-300" size={64} />
          <h2 className="text-2xl font-semibold mb-4">No Vendor Profile Found</h2>
          <p className="text-stone-600 mb-6">Register as a vendor to start receiving bookings</p>
          <Button onClick={() => navigate('/vendor-register')} className="bg-primary hover:bg-primary/90 rounded-full">
            Register as Vendor
          </Button>
        </Card>
      </div>
    );
  }

  // ── Grocery / Product vendor ─────────────────────────────────────
  if (isProductVendor(vendor)) {
    return (
      <GroceryVendorDashboard
        vendor={vendor}
        groceryItems={groceryItems}
        groceryOrders={groceryOrders}
        groceryLoading={groceryLoading}
        newItem={newItem}
        earnings={earnings}
        payouts={payouts}
        payoutAmount={payoutAmount}
        payoutSubmitting={payoutSubmitting}
        onNewItemChange={setNewItem}
        onAddItem={handleAddGroceryItem}
        onUpdateStock={handleUpdateStock}
        onPayoutAmountChange={setPayoutAmount}
        onRequestPayout={handleRequestPayout}
      />
    );
  }

  // ── Service vendor ───────────────────────────────────────────────
  const statusColors = {
    pending: 'bg-amber-100 text-amber-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    suspended: 'bg-stone-100 text-stone-800',
  };
  const vendorStatus = vendor.status || 'approved';
  const pendingQuotes = quotes.filter(q => q.status === 'pending').length;
  const onboardingMissing = vendor.onboarding_missing_required || [];
  const onboardingStatus = vendor.onboarding_status || 'complete';
  const onboardingProgress = onboardingMissing.length === 0 ? 100 : Math.max(20, 100 - onboardingMissing.length * 10);
  const categoryTabLabel = (() => {
    switch (categoryTabValue) {
      case 'category-venue': return 'Venue Basics';
      case 'category-dj': return 'DJ Setup';
      case 'category-caterer': return 'Caterer Menu';
      case 'category-photography': return 'Photo Delivery';
      case 'category-decorator': return 'Decor Themes';
      case 'category-mehandi': return 'Mehandi Styles';
      default: return null;
    }
  })();

  const sectionMap = {
    delivery_radius: 'grocery', delivery_schedule: 'grocery', product_catalog: 'grocery',
    quality_grade: 'grocery', minimum_order_quantity: 'grocery',
    venue_types: 'venues', amenities: 'venues', capacity_min: 'venues', capacity_max: 'venues',
    pricing_model: 'venues', pricing_options: 'venues', availability_calendar: 'venues', cancellation_policy: 'venues',
    specializations: 'makeup', service_menu: 'makeup', pricing: 'makeup',
    services: 'photography', packages: 'photography', delivery_timeline: 'photography',
    fleet_details: 'transport', vehicle_categories: 'transport', pricing_structure: 'transport', insurance_coverage: 'transport',
    design_styles: 'mehandi', quality_type: 'mehandi', application_time_estimates: 'mehandi',
  };

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-7xl mx-auto w-full px-4 md:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight font-heading">
              {vendor.business_name}
            </h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[vendorStatus] || statusColors.approved}`}>
              {vendorStatus.toUpperCase()}
            </span>
          </div>
          <p className="text-lg text-stone-600 mt-2">Manage your services and bookings</p>
          {vendorStatus === 'pending' && (
            <p className="text-amber-600 text-sm mt-2">Your profile is under review. You will receive an email once approved.</p>
          )}
        </div>

        {onboardingStatus !== 'complete' && (
          <Card className="p-6 bg-white rounded-2xl border border-amber-200 mb-8">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <p className="text-sm uppercase tracking-wide text-amber-700">Onboarding Progress</p>
                <p className="text-2xl font-semibold text-stone-900">{onboardingProgress}% Complete</p>
                {onboardingMissing.length > 0 && (
                  <p className="text-sm text-amber-700 mt-2">Missing: {onboardingMissing.join(', ')}</p>
                )}
              </div>
              <Button onClick={() => navigate('/vendor-onboarding')} className="bg-amber-600 hover:bg-amber-700 rounded-full">
                Complete Onboarding
              </Button>
            </div>
            {onboardingMissing.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {onboardingMissing.slice(0, 4).map((field) => (
                  <Button key={field} variant="outline" size="sm" onClick={() => navigate(`/vendor-onboarding?section=${sectionMap[field] || 'core'}`)} className="border-amber-200 text-amber-700">
                    Fix {field}
                  </Button>
                ))}
              </div>
            )}
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard icon={Star} value={vendor.rating.toFixed(1)} label="Average Rating" bgColor="bg-secondary/10" />
          <StatCard icon={Package} value={packages.length} label="Active Packages" bgColor="bg-primary/10" />
          <StatCard icon={MessageSquare} value={pendingQuotes} label="Pending Quotes" bgColor="bg-accent/10" />
          <StatCard icon={TrendingUp} value={`${Math.round((vendor.acceptance_rate || 0) * 100)}%`} label="Acceptance Rate" bgColor="bg-emerald-100" />
        </div>
        {earnings && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
            <StatCard icon={Package} value={earnings.total_orders} label="Total Orders" bgColor="bg-primary/10" />
            <StatCard icon={TrendingUp} value={formatCurrency(earnings.commission_deducted)} label="Commission Deducted" bgColor="bg-amber-100" />
            <StatCard icon={Star} value={formatCurrency(earnings.net_earnings)} label="Net Earnings" bgColor="bg-emerald-100" />
            <StatCard icon={MessageSquare} value={formatCurrency(earnings.payout_balance)} label="Payout Balance" bgColor="bg-secondary/10" />
            <StatCard icon={MessageSquare} value={formatCurrency(earnings.withdrawn_total)} label="Withdrawn Total" bgColor="bg-stone-100" />
          </div>
        )}

        <Tabs value={tabValue} onValueChange={setTabValue} className="w-full">
          <TabsList className="w-full justify-start bg-white rounded-xl p-1 mb-8">
            {categoryTabValue && <TabsTrigger value={categoryTabValue} className="rounded-lg">{categoryTabLabel}</TabsTrigger>}
            <TabsTrigger value="bookings" className="rounded-lg">Bookings ({pendingBookings.length})</TabsTrigger>
            <TabsTrigger value="packages" className="rounded-lg">Packages</TabsTrigger>
            <TabsTrigger value="quotes" className="rounded-lg">Quote Requests</TabsTrigger>
            <TabsTrigger value="pricing" className="rounded-lg">Pricing Rules</TabsTrigger>
            <TabsTrigger value="payouts" className="rounded-lg">Payouts</TabsTrigger>
            <TabsTrigger value="profile" className="rounded-lg">Profile</TabsTrigger>
          </TabsList>

          {/* Category-specific tabs (extracted) */}
          {categoryTabValue === 'category-venue' && <TabsContent value="category-venue"><VenueTab vendor={vendor} loading={loading} navigate={navigate} /></TabsContent>}
          {categoryTabValue === 'category-dj' && <TabsContent value="category-dj"><DJTab vendor={vendor} loading={loading} navigate={navigate} /></TabsContent>}
          {categoryTabValue === 'category-caterer' && <TabsContent value="category-caterer"><CatererTab vendor={vendor} loading={loading} navigate={navigate} /></TabsContent>}
          {categoryTabValue === 'category-photography' && <TabsContent value="category-photography"><PhotographyTab vendor={vendor} loading={loading} navigate={navigate} /></TabsContent>}
          {categoryTabValue === 'category-decorator' && <TabsContent value="category-decorator"><DecoratorTab vendor={vendor} loading={loading} navigate={navigate} /></TabsContent>}
          {categoryTabValue === 'category-mehandi' && <TabsContent value="category-mehandi"><MehandiTab vendor={vendor} loading={loading} navigate={navigate} /></TabsContent>}

          {/* Bookings tab (extracted) */}
          <TabsContent value="bookings">
            <BookingsTab
              bookings={bookings}
              pendingBookings={pendingBookings}
              confirmedBookings={confirmedBookings}
              onAccept={handleAcceptBooking}
              onReject={handleRejectBooking}
              onEmergencyCancel={handleEmergencyCancel}
              navigate={navigate}
            />
          </TabsContent>

          {/* Packages tab */}
          <TabsContent value="packages">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold">My Packages</h2>
              <Button onClick={() => navigate('/create-package')} className="bg-primary hover:bg-primary/90 rounded-full">
                <Plus size={18} className="mr-2" /> Create Package
              </Button>
            </div>
            {packages.length === 0 ? (
              <Card className="p-12 text-center bg-white rounded-2xl">
                <Package className="mx-auto mb-4 text-stone-300" size={48} />
                <p className="text-stone-500 mb-4">No packages yet</p>
                <Button onClick={() => navigate('/create-package')} className="bg-primary hover:bg-primary/90 rounded-full">
                  Create Your First Package
                </Button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {packages.map((pkg) => (
                  <PackageCard key={pkg.id} pkg={pkg} onEdit={(id) => navigate(`/packages/${id}/edit`)} />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Quotes tab */}
          <TabsContent value="quotes">
            <h2 className="text-2xl font-semibold mb-6">Quote Requests</h2>
            {quotes.length === 0 ? (
              <Card className="p-12 text-center bg-white rounded-2xl">
                <MessageSquare className="mx-auto mb-4 text-stone-300" size={48} />
                <p className="text-stone-500">No quote requests yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {quotes.map((quote) => (
                  <Card key={quote.id} className="p-6 bg-white rounded-2xl border border-stone-100">
                    <h3 className="text-xl font-semibold mb-2">Quote Request</h3>
                    <p className="text-stone-600 mb-4">Services: {quote.requested_services.join(', ')}</p>
                    {quote.lead_score_label && (
                      <div className="mb-4">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                          quote.lead_score_label === 'Hot'
                            ? 'bg-rose-100 text-rose-700'
                            : quote.lead_score_label === 'Warm'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-stone-100 text-stone-600'
                        }`}>
                          {quote.lead_score_label} Lead
                        </span>
                        {quote.lead_score !== undefined && (
                          <span className="ml-2 text-sm text-stone-500">Score: {quote.lead_score}</span>
                        )}
                      </div>
                    )}
                    {quote.status === 'pending' && (
                      <Button onClick={() => navigate(`/quotes/${quote.id}/respond`)} className="bg-primary hover:bg-primary/90 rounded-lg">
                        Respond to Quote
                      </Button>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Pricing rules tab (extracted) */}
          <TabsContent value="pricing">
            <PricingRulesTab
              pricingRules={pricingRules}
              pricingSaving={pricingSaving}
              onAddRule={handleAddPricingRule}
              onUpdateRule={handleUpdatePricingRule}
              onRemoveRule={handleRemovePricingRule}
              onSaveRules={handleSavePricingRules}
            />
          </TabsContent>

          {/* Payouts tab (extracted) */}
          <TabsContent value="payouts">
            <PayoutsTab
              earnings={earnings}
              payouts={payouts}
              payoutAmount={payoutAmount}
              payoutSubmitting={payoutSubmitting}
              onPayoutAmountChange={setPayoutAmount}
              onRequestPayout={handleRequestPayout}
            />
          </TabsContent>

          {/* Profile tab */}
          <TabsContent value="profile">
            <Card className="p-8 bg-white rounded-2xl">
              <h2 className="text-2xl font-semibold mb-6">Vendor Profile</h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-stone-500 uppercase tracking-wider mb-1">Business Name</p>
                  <p className="text-lg font-medium">{vendor.business_name}</p>
                </div>
                {vendor.description && (
                  <div>
                    <p className="text-sm text-stone-500 uppercase tracking-wider mb-1">Description</p>
                    <p className="text-stone-600">{vendor.description}</p>
                  </div>
                )}
                <div className="pt-4">
                  <Button onClick={() => navigate(`/vendors/${vendor.id}/edit`)} className="bg-primary hover:bg-primary/90 rounded-lg">
                    Edit Profile
                  </Button>
                  <Button onClick={() => navigate('/vendor-onboarding?section=core')} variant="outline" className="ml-3 rounded-lg">
                    Complete Onboarding
                  </Button>
                </div>
                <div className="pt-4 border-t border-stone-200">
                  <p className="text-sm text-stone-500 uppercase tracking-wider mb-2">Verification</p>
                  <p className="text-stone-600 mb-3">
                    Status: {vendor.verification_status || (vendor.is_verified ? 'approved' : 'not_submitted')}
                  </p>
                  <input
                    type="file"
                    onChange={(e) => handleVerificationUpload(e.target.files?.[0])}
                    disabled={verificationUploading}
                    className="block text-sm text-stone-600"
                  />
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>

        {selectedBooking && (
          <EmergencyCancelModal
            booking={selectedBooking}
            isOpen={showEmergencyModal}
            onClose={() => {
              setShowEmergencyModal(false);
              setSelectedBooking(null);
            }}
            onSubmit={handleEmergendaryCancelSubmit}
          />
        )}
      </div>
      <AssistantWidget role="vendor" context={{ vendor }} title="Vendor Assistant" />
    </div>
  );
};

export default VendorDashboard;
