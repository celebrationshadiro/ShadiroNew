import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../lib/apiClient';
import { useBookingFlow } from '../../hooks/useBookingFlow';

const CATEGORY_META_CONFIG = {
  photography: [
    { key: 'shoot_type', label: 'Shoot Type', type: 'select', options: ['wedding', 'portrait', 'event'] },
    { key: 'hours_required', label: 'Hours Required', type: 'number' },
  ],
  catering: [
    { key: 'menu_type', label: 'Menu Type', type: 'select', options: ['veg', 'nonveg', 'both'] },
    { key: 'meals_count', label: 'Meals Count', type: 'number' },
    { key: 'cuisine_type', label: 'Cuisine Type', type: 'text' },
  ],
  decoration: [
    { key: 'theme', label: 'Theme', type: 'text' },
    { key: 'venue_size_sqft', label: 'Venue Size (sqft)', type: 'number' },
    { key: 'decoration_type', label: 'Decoration Type', type: 'text' },
  ],
  makeup: [
    { key: 'service_type', label: 'Service Type', type: 'select', options: ['bridal', 'party', 'editorial'] },
    { key: 'artists_count', label: 'Artists Count', type: 'number' },
  ],
  lighting: [
    { key: 'lighting_type', label: 'Lighting Type', type: 'text' },
    { key: 'setup_hours', label: 'Setup Hours', type: 'number' },
    { key: 'equipment_list', label: 'Equipment (comma separated)', type: 'text' },
  ],
  videography: [
    { key: 'video_type', label: 'Video Type', type: 'text' },
    { key: 'hours_required', label: 'Hours Required', type: 'number' },
    { key: 'drone_required', label: 'Drone Required', type: 'select', options: ['true', 'false'] },
  ],
};

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

function normalizeCategorySlug(vendor) {
  const raw = String(vendor?.category_slug || vendor?.category_name || vendor?.category_id || '').toLowerCase().trim();
  const value = raw.replace(/\s+/g, '_');
  const aliases = { decor: 'decoration', decorator: 'decoration', makeup_artist: 'makeup' };
  return aliases[value] || value || 'photography';
}

function unwrap(res) {
  if (res && typeof res === 'object' && Object.prototype.hasOwnProperty.call(res, 'data')) {
    if (res.success === false) return null;
    return res.data;
  }
  return res;
}

export default function ServiceBookingPage() {
  const { vendorId } = useParams();
  const navigate = useNavigate();

  const [vendor, setVendor] = useState(null);
  const [packages, setPackages] = useState([]);
  const [loadingPage, setLoadingPage] = useState(true);
  const [uiError, setUiError] = useState('');
  const [step, setStep] = useState(1);
  const [createdBooking, setCreatedBooking] = useState(null);

  const categorySlug = useMemo(() => normalizeCategorySlug(vendor), [vendor]);
  const metaFields = useMemo(() => CATEGORY_META_CONFIG[categorySlug] || [], [categorySlug]);
  const { createIntent, payNow, loading, error } = useBookingFlow(categorySlug);

  const [form, setForm] = useState({
    package_id: '',
    event_date: '',
    event_time: '',
    guest_count: 100,
    notes: '',
    amount_paise: 0,
    category_meta: {},
  });

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoadingPage(true);
      setUiError('');
      try {
        const vendorRes = await apiClient.get(`/vendors/${vendorId}`);
        const vendorData = unwrap(vendorRes);
        const packagesRes = await apiClient.get(`/vendors/${vendorId}/packages`);
        const packageData = unwrap(packagesRes);
        if (!mounted) return;
        setVendor(vendorData || null);
        setPackages(Array.isArray(packageData) ? packageData : []);
      } catch (err) {
        if (mounted) setUiError(err?.response?.data?.detail || err.message || 'Unable to load booking data');
      } finally {
        if (mounted) setLoadingPage(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [vendorId]);

  const selectedPackage = useMemo(
    () => packages.find((pkg) => String(pkg?.id) === String(form.package_id)),
    [packages, form.package_id],
  );

  useEffect(() => {
    if (!selectedPackage) return;
    const byPaise = Number(selectedPackage?.price_paise || selectedPackage?.amount_paise || 0);
    const byRupee = Number(selectedPackage?.price || selectedPackage?.amount || 0) * 100;
    const resolved = Number.isFinite(byPaise) && byPaise > 0 ? byPaise : Math.round(byRupee);
    setForm((prev) => ({ ...prev, amount_paise: resolved > 0 ? resolved : prev.amount_paise }));
  }, [selectedPackage]);

  const setMetaValue = (key, value) => {
    setForm((prev) => ({
      ...prev,
      category_meta: { ...(prev.category_meta || {}), [key]: value },
    }));
  };

  const onContinue = async (e) => {
    e.preventDefault();
    setUiError('');
    if (!form.package_id || !form.event_date || !form.event_time || !form.amount_paise) {
      setUiError('Package, date, time and amount are required');
      return;
    }
    setStep(2);
  };

  const onPayNow = async () => {
    setUiError('');
    try {
      const intentRes = await createIntent({
        vendor_id: vendorId,
        package_id: form.package_id,
        category_slug: categorySlug,
        event_date: form.event_date,
        event_time: form.event_time,
        guest_count: Number(form.guest_count || 1),
        notes: form.notes,
        amount_paise: Number(form.amount_paise),
        category_meta: form.category_meta || {},
      });
      const created = unwrap(intentRes);
      setCreatedBooking(created || null);

      const intentId = created?.intent_id || created?.booking_intent_id;
      if (!intentId) {
        navigate(`/bookings/${created?.id || created?.booking_id || ''}/tracking`);
        return;
      }

      const payRes = await payNow({ intent_id: intentId });
      const payData = unwrap(payRes);
      const orderId = payData?.razorpay_order_id || payData?.order_id;
      const amount = payData?.amount_paise || payData?.amount;
      const key = payData?.key_id;
      if (!orderId || !amount || !key) {
        navigate(`/bookings/${created?.id || created?.booking_id || intentId}/tracking`);
        return;
      }

      const loaded = await loadRazorpayScript();
      if (!loaded) {
        throw new Error('Unable to load payment gateway');
      }

      const razorpay = new window.Razorpay({
        key,
        amount,
        currency: payData?.currency || 'INR',
        name: vendor?.business_name || 'Service Booking',
        description: 'Advance payment',
        order_id: orderId,
        handler: () => {
          navigate(`/bookings/${created?.id || created?.booking_id || intentId}/tracking`);
        },
        theme: { color: '#111827' },
      });
      razorpay.open();
    } catch (err) {
      setUiError(err?.response?.data?.detail || err.message || 'Booking failed');
    }
  };

  if (loadingPage) return <div className="max-w-2xl mx-auto p-4">Loading booking page...</div>;
  if (uiError && !vendor) return <div className="max-w-2xl mx-auto p-4 text-red-600">{uiError}</div>;

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <div className="bg-white border rounded-xl p-4">
        <h1 className="text-xl font-semibold">Book {vendor?.business_name || 'Vendor'}</h1>
        <p className="text-sm text-stone-600">
          2-step fast booking | Vendor response SLA: 4 hours | Category: {categorySlug}
        </p>
      </div>

      {step === 1 ? (
        <form onSubmit={onContinue} className="bg-white border rounded-xl p-4 space-y-3">
          <label className="block text-sm font-medium">Package</label>
          <select
            className="w-full border rounded p-2"
            value={form.package_id}
            onChange={(e) => setForm((prev) => ({ ...prev, package_id: e.target.value }))}
            required
          >
            <option value="">Select package</option>
            {packages.map((pkg) => (
              <option key={pkg.id} value={pkg.id}>
                {pkg.name || pkg.title || pkg.id}
              </option>
            ))}
          </select>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium">Event Date</label>
              <input
                type="date"
                className="w-full border rounded p-2"
                value={form.event_date}
                onChange={(e) => setForm((prev) => ({ ...prev, event_date: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium">Event Time</label>
              <input
                type="time"
                className="w-full border rounded p-2"
                value={form.event_time}
                onChange={(e) => setForm((prev) => ({ ...prev, event_time: e.target.value }))}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium">Guest Count</label>
              <input
                type="number"
                min="1"
                className="w-full border rounded p-2"
                value={form.guest_count}
                onChange={(e) => setForm((prev) => ({ ...prev, guest_count: Number(e.target.value || 1) }))}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium">Amount (INR)</label>
              <input
                type="number"
                min="1"
                className="w-full border rounded p-2"
                value={Math.floor((form.amount_paise || 0) / 100)}
                onChange={(e) => setForm((prev) => ({ ...prev, amount_paise: Number(e.target.value || 0) * 100 }))}
                required
              />
            </div>
          </div>

          {metaFields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm font-medium">{field.label}</label>
              {field.type === 'select' ? (
                <select
                  className="w-full border rounded p-2"
                  value={String(form.category_meta?.[field.key] ?? '')}
                  onChange={(e) => setMetaValue(field.key, e.target.value)}
                  required
                >
                  <option value="">Select</option>
                  {field.options.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type}
                  className="w-full border rounded p-2"
                  value={String(form.category_meta?.[field.key] ?? '')}
                  onChange={(e) => setMetaValue(field.key, field.type === 'number' ? Number(e.target.value || 0) : e.target.value)}
                  required
                />
              )}
            </div>
          ))}

          <div>
            <label className="block text-sm font-medium">Notes (optional)</label>
            <textarea
              className="w-full border rounded p-2"
              rows={3}
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
            />
          </div>

          {uiError ? <p className="text-sm text-red-600">{uiError}</p> : null}
          <button className="w-full bg-black text-white rounded p-2" type="submit">
            Continue
          </button>
        </form>
      ) : (
        <div className="bg-white border rounded-xl p-4 space-y-3">
          <h2 className="text-lg font-semibold">Review & Pay</h2>
          <div className="text-sm text-stone-700">
            <p>Package: {selectedPackage?.name || selectedPackage?.title || form.package_id}</p>
            <p>Date: {form.event_date}</p>
            <p>Time: {form.event_time}</p>
            <p>Guests: {form.guest_count}</p>
            <p>Amount: Rs. {Math.floor((form.amount_paise || 0) / 100)}</p>
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          {uiError ? <p className="text-sm text-red-600">{uiError}</p> : null}
          {createdBooking?.id ? (
            <p className="text-sm text-green-700">Booking request created: {createdBooking.id}</p>
          ) : null}
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              className="w-full border rounded p-2"
              onClick={() => setStep(1)}
              disabled={loading}
            >
              Back
            </button>
            <button
              type="button"
              className="w-full bg-black text-white rounded p-2 disabled:opacity-60"
              onClick={onPayNow}
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Pay & Book'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

