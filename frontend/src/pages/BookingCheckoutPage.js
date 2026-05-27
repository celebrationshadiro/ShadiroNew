import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { vendors as vendorsApi, packages as packagesApi, orders as ordersApi, payments as paymentsApi, events as eventsApi } from '../lib/api';
import { isProductVendor } from '../lib/vendorType';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ArrowLeft, ShieldCheck, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Textarea } from '../components/ui/textarea';

const ServiceItem = ({ service, checked, onToggle }) => (
  <div className="flex items-center gap-3">
    <Checkbox id={service} checked={checked} onCheckedChange={onToggle} />
    <Label htmlFor={service} className="cursor-pointer">{service}</Label>
  </div>
);

const BookingSummary = ({ total, onCheckout, submitting, disabled }) => (
  <Card className="p-6 bg-white rounded-2xl border border-stone-100 sticky top-8">
    <h2 className="text-2xl font-semibold mb-6">Order Summary</h2>
    
    <div className="space-y-4 mb-6 pb-6 border-b border-stone-200">
      <div className="flex justify-between">
        <span className="text-stone-600">Subtotal</span>
        <span className="font-medium">₹{total.toLocaleString()}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-stone-600">Service Fee</span>
        <span className="font-medium">₹0</span>
      </div>
    </div>

    <div className="flex justify-between mb-6">
      <span className="text-xl font-semibold">Total Amount</span>
      <span className="text-2xl font-bold text-primary">₹{total.toLocaleString()}</span>
    </div>

    {total === 0 && (
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg mb-4">
        <p className="text-sm text-amber-900">⚠️ Amount is ₹0. Ensure vendor details are loaded.</p>
      </div>
    )}

    <Button
      onClick={onCheckout}
      className="w-full bg-primary hover:bg-primary/90 h-14 rounded-full text-lg font-medium disabled:opacity-50"
      disabled={submitting || disabled || total === 0}
      data-testid="proceed-to-payment-button"
    >
      {submitting ? 'Processing...' : total > 0 ? 'Proceed to Payment' : 'Select Event & Services'}
    </Button>

    <div className="mt-6 p-4 bg-stone-50 rounded-lg">
      <p className="text-sm text-stone-600 text-center">
        🔒 Secure payment powered by Razorpay
      </p>
    </div>
  </Card>
);

const BookingCheckoutPage = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [vendor, setVendor] = useState(null);
  const [packageData, setPackageData] = useState(null);
  const [selectedServices, setSelectedServices] = useState([]);
  const [customItems, setCustomItems] = useState([]);
  const [pricingMode, setPricingMode] = useState('base');
  const [eventId, setEventId] = useState('');
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [venueType, setVenueType] = useState('');
  const [mapLocation, setMapLocation] = useState({ lat: '', lng: '' });
  const [eventLocationNotes, setEventLocationNotes] = useState('');
  const [selectedAddOns, setSelectedAddOns] = useState([]);

  const vendorId = searchParams.get('vendor_id');
  const packageId = searchParams.get('package_id');

  const loadUserEvents = useCallback(async () => {
    setLoadingEvents(true);
    try {
      const eventsRes = await eventsApi.getAll();
      
      // Ensure data is an array, not an error object
      let userEvents = [];
      if (eventsRes?.data && Array.isArray(eventsRes.data)) {
        userEvents = eventsRes.data;
      } else if (eventsRes?.data && typeof eventsRes.data === 'object') {
        // If data is an error object, treat as empty
        console.warn('Unexpected response format:', eventsRes.data);
        userEvents = [];
      }
      
      setEvents(userEvents);
      
      // Auto-select the most recent upcoming event
      if (userEvents.length > 0) {
        const upcomingEvents = userEvents
          .filter(e => {
            try {
              return new Date(e.date) > new Date();
            } catch {
              return false;
            }
          })
          .sort((a, b) => {
            try {
              return new Date(a.date) - new Date(b.date);
            } catch {
              return 0;
            }
          });
        
        const eventToSelect = upcomingEvents[0] || userEvents[0];
        setSelectedEvent(eventToSelect);
        setEventId(eventToSelect._id || eventToSelect.id);
      }
    } catch (error) {
      console.error('Failed to load events:', error);
      setEvents([]); // Ensure events is always an array
    } finally {
      setLoadingEvents(false);
    }
  }, []);

  const loadBookingData = useCallback(async () => {
    setLoading(true);
    try {
      const state = location.state || {};
      if (state.customItems && Array.isArray(state.customItems)) {
        setCustomItems(state.customItems);
        setSelectedServices(state.customItems.map((i) => i.name).filter(Boolean));
        setPricingMode(state.pricingMode || 'custom');
      }
      if (state.selectedAddOns && Array.isArray(state.selectedAddOns)) {
        setSelectedAddOns(state.selectedAddOns);
      }
      if (state.selectedServices && Array.isArray(state.selectedServices) && state.selectedServices.length > 0) {
        setSelectedServices(state.selectedServices);
      }
      if (vendorId) {
        const vendorRes = await vendorsApi.getById(vendorId);
        if (isProductVendor(vendorRes.data)) {
          toast.error('Grocery vendors use a cart checkout');
          navigate(`/vendors/${vendorId}`);
          return;
        }
        setVendor(vendorRes.data);
        if (!state.selectedServices && !state.customItems) {
          setSelectedServices(vendorRes.data.services || []);
        }
      }
      if (packageId) {
        const pkgRes = await packagesApi.getById(packageId);
        setPackageData(pkgRes.data);
        setSelectedServices(pkgRes.data.services_included || []);
        setPricingMode('package');
      }
    } catch (error) {
      console.error('Failed to load booking data:', error);
      toast.error('Failed to load booking details');
    } finally {
      setLoading(false);
    }
  }, [location.state, vendorId, packageId, navigate]);

  useEffect(() => {
    if (!user) {
      toast.error('Please login to continue');
      navigate('/auth');
      return;
    }
    loadBookingData();
    loadUserEvents();
  }, [user, navigate, loadBookingData, loadUserEvents]);

  const calculateTotal = () => {
    if (pricingMode === 'custom' && customItems.length > 0) {
      return customItems.reduce((sum, item) => {
        const qty = item.quantity || item.qty || 1;
        const unitPrice = item.unit_price || item.unitPrice || 0;
        const total = item.total_price || (unitPrice * qty);
        return sum + total;
      }, 0);
    }
    if (packageData && packageData.price) {
      return packageData.price;
    }
    if (vendor) {
      // Use min_price if available (from vendor improvements)
      if (vendor.min_price) {
        return vendor.min_price;
      }
      // Fallback to base_price * services
      if (vendor.base_price) {
        return vendor.base_price * Math.max(selectedServices.length, 1);
      }
    }
    return 0; // Default fallback
  };

  const handleServiceToggle = (service) => {
    setSelectedServices(prev => 
      prev.includes(service) ? prev.filter(s => s !== service) : [...prev, service]
    );
  };

  const loadRazorpay = () => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleCheckout = async () => {
    if (!eventId) {
      toast.error('Please select an event');
      return;
    }

    let eventPayload = selectedEvent;
    if (!eventPayload && eventId) {
      try {
        const ev = await eventsApi.getById(eventId);
        eventPayload = ev.data;
      } catch {
        toast.error('Event details not found. Please create an event with location & date.');
        return;
      }
    }
    const eventCity = eventPayload?.city || eventPayload?.location;
    if (!eventCity && !eventLocationNotes) {
      toast.error('Add an event city/location so vendors can reach you.');
      return;
    }
    if (!eventPayload?.date) {
      toast.error('Event date is required for service booking.');
      return;
    }

    if (selectedServices.length === 0 && customItems.length === 0) {
      toast.error('Please select at least one service');
      return;
    }

    const total = calculateTotal();
    if (total === 0) {
      toast.error('Invalid booking amount. Please check vendor details.');
      return;
    }

    setSubmitting(true);
    try {
      const totalPaise = Math.round(calculateTotal() * 100);
      const orderData = {
        user_id: user.id,
        vendor_id: vendorId,
        event_id: eventId,
        package_id: packageId || null,
        total_amount: calculateTotal(),
        total_amount_paise: totalPaise,
        amount_paise: totalPaise,
        services: selectedServices,
        selected_items: customItems,
        pricing_mode: pricingMode,
        booking_context: 'SERVICE',
        venue_type: venueType || null,
        event_city: eventCity || null,
        event_location: eventPayload?.location || eventCity || null,
        event_date: eventPayload?.date || null,
        event_location_lat: mapLocation.lat || null,
        event_location_lng: mapLocation.lng || null,
        event_location_notes: eventLocationNotes || null,
      };

      const orderRes = await ordersApi.create(orderData);
      const order = orderRes.data;
      const intentId = order?.id || order?.booking_intent_id || order?.order_id;

      const razorpayRes = await paymentsApi.createOrder(intentId);
      const { razorpay_order_id, amount_paise, currency, key_id } = razorpayRes.data;

      const res = await loadRazorpay();
      if (!res) {
        toast.error('Failed to load payment gateway');
        return;
      }

      const options = {
        key: key_id,
        amount: amount_paise,
        currency: currency,
        name: 'Shadiro',
        description: `Booking for ${vendor?.business_name || 'Event Services'}`,
        order_id: razorpay_order_id,
        handler: async function (response) {
          try {
            const verified = await paymentsApi.verify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              booking_intent_id: intentId,
            });
            toast.success('Payment successful! Booking confirmed.');
            const bookingId = verified?.data?.booking_id || verified?.booking_id || intentId;
            navigate(`/bookings/${bookingId}/tracking`);
          } catch (error) {
            console.error('Payment verification failed:', error);
            toast.error('Payment verification failed');
          }
        },
        prefill: {
          name: user.name,
          email: user.email,
          contact: user.phone || '',
        },
        theme: {
          color: '#BE185D',
        },
      };

      const paymentObject = new window.Razorpay(options);
      paymentObject.open();
    } catch (error) {
      console.error('Checkout failed:', error);
      toast.error(error.response?.data?.detail || 'Checkout failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500 text-lg">Loading...</p>
      </div>
    );
  }

  const total = calculateTotal();

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-5xl mx-auto w-full px-4 md:px-8 py-8">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-6" data-testid="back-button">
          <ArrowLeft size={18} className="mr-2" /> Back
        </Button>

        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight mb-8 font-heading">
          Complete Your Booking
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 bg-white rounded-2xl border border-stone-100">
              <h2 className="text-2xl font-semibold mb-4">Booking Details</h2>
              
              {vendor && (
                <div className="mb-6 pb-6 border-b border-stone-200">
                  <h3 className="text-xl font-medium mb-2">{vendor.business_name}</h3>
                  {vendor.location && <p className="text-stone-600">{vendor.location}</p>}
                </div>
              )}

              {packageData && (
                <div className="mb-6 pb-6 border-b border-stone-200">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xl font-medium">{packageData.name}</h3>
                    <div className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
                      {packageData.tier.toUpperCase()}
                    </div>
                  </div>
                  {packageData.description && (
                    <p className="text-stone-600 text-sm">{packageData.description}</p>
                  )}
                </div>
              )}

              <div className="mb-6">
                <Label htmlFor="event-id" className="mb-2 block">Event Location & Date *</Label>
                {loadingEvents ? (
                  <div className="h-12 rounded-lg bg-stone-100 flex items-center px-4">
                    <p className="text-stone-500 text-sm">Loading your events...</p>
                  </div>
                ) : events.length > 0 ? (
                  <Select value={eventId} onValueChange={(value) => {
                    setEventId(value);
                    const selected = events.find(e => (e._id || e.id) === value);
                    setSelectedEvent(selected);
                  }}>
                    <SelectTrigger className="h-12 rounded-lg">
                      <SelectValue placeholder="Choose your event" />
                    </SelectTrigger>
                    <SelectContent>
                      {events.map((event) => (
                        <SelectItem key={event._id || event.id} value={event._id || event.id}>
                          <div className="flex items-center gap-2">
                            <span>{event.title || event.name}</span>
                            <span className="text-xs text-stone-500">
                              {new Date(event.date).toLocaleDateString()}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <div className="space-y-4">
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
                      <AlertCircle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-amber-900">No events found</p>
                        <p className="text-xs text-amber-700 mt-2">
                          <button 
                            onClick={() => navigate('/create-event')}
                            className="underline hover:no-underline font-medium"
                          >
                            Create an event first
                          </button>
                        </p>
                      </div>
                    </div>
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-stone-200"></div>
                      </div>
                      <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-stone-500">or enter manually</span>
                      </div>
                    </div>
                    <Input
                      placeholder="Enter event ID manually"
                      className="h-12 rounded-lg"
                      value={eventId}
                      onChange={(e) => setEventId(e.target.value)}
                    />
                  </div>
                )}
                {selectedEvent && (
                  <div className="text-sm text-stone-600 mt-3 space-y-1">
                    <p>Date: {new Date(selectedEvent.date).toLocaleDateString(undefined, { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}</p>
                    <p>Event Location: {selectedEvent.city || selectedEvent.location || 'Not set'}</p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <Label className="mb-2 block">Venue Type</Label>
                  <Select value={venueType} onValueChange={setVenueType}>
                    <SelectTrigger className="h-12 rounded-lg">
                      <SelectValue placeholder="Home, hall, or open ground" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="home">Home</SelectItem>
                      <SelectItem value="hall">Hall</SelectItem>
                      <SelectItem value="open_ground">Open Ground</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-stone-500 mt-2">Helps the vendor prepare correct setup.</p>
                </div>
                <div>
                  <Label className="mb-2 block">Map Pin (optional)</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      placeholder="Lat"
                      value={mapLocation.lat}
                      onChange={(e) => setMapLocation({ ...mapLocation, lat: e.target.value })}
                      className="h-12 rounded-lg"
                    />
                    <Input
                      placeholder="Lng"
                      value={mapLocation.lng}
                      onChange={(e) => setMapLocation({ ...mapLocation, lng: e.target.value })}
                      className="h-12 rounded-lg"
                    />
                  </div>
                  <p className="text-xs text-stone-500 mt-2">Add if you want precise arrival; optional.</p>
                </div>
              </div>

              <div className="mb-6">
                <Label className="mb-2 block">Event Location Notes (optional)</Label>
                <Textarea
                  className="rounded-lg"
                  rows={3}
                  placeholder="Landmark, floor, parking instructions"
                  value={eventLocationNotes}
                  onChange={(e) => setEventLocationNotes(e.target.value)}
                />
                <p className="text-xs text-stone-500 mt-1">Used only for on-site service; not for delivery.</p>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-4">Selected Services</h3>
                {pricingMode === 'custom' && customItems.length > 0 ? (
                  <ul className="space-y-2">
                    {customItems.map((item, idx) => (
                      <li key={idx} className="flex items-center justify-between text-stone-600">
                        <span>{item.name} {item.quantity ? `x${item.quantity}` : ''}</span>
                        <span className="text-stone-800 font-medium">₹{(item.total_price || (item.unit_price * (item.quantity || 1))).toLocaleString()}</span>
                      </li>
                    ))}
                  </ul>
                ) : packageData ? (
                  <ul className="space-y-2">
                    {packageData.services_included.map((service, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-stone-600">
                        <ShieldCheck size={16} className="text-primary" />
                        {service}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="space-y-3">
                    {(vendor?.services || []).map((service, idx) => (
                      <ServiceItem
                        key={idx}
                        service={service}
                        checked={selectedServices.includes(service)}
                        onToggle={() => handleServiceToggle(service)}
                      />
                    ))}
                  </div>
                )}
                {selectedAddOns.length > 0 && (
                  <div className="mt-4 p-3 rounded-lg bg-stone-50 border border-stone-200">
                    <p className="text-sm font-medium text-stone-700 mb-2">Add-ons (billed by vendor)</p>
                    <p className="text-xs text-stone-500">These extras will be confirmed with the vendor; not charged in this payment.</p>
                  </div>
                )}
              </div>
            </Card>
          </div>

          <div>
            <BookingSummary
              total={total}
              onCheckout={handleCheckout}
              submitting={submitting}
              disabled={!eventId || selectedServices.length === 0}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookingCheckoutPage;
