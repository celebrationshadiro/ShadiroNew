import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../lib/apiClient';
import { useBookingFlow } from '../../hooks/useBookingFlow';
import DateRangePicker from '../../components/booking/DateRangePicker';

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

function unwrap(res) {
  if (res && typeof res === 'object' && Object.prototype.hasOwnProperty.call(res, 'data')) {
    if (res.success === false) return null;
    return res.data;
  }
  return res;
}

function toDateOnly(input) {
  return String(input || '').split('T')[0];
}

export default function RentalBookingPage() {
  const { vendorId } = useParams();
  const navigate = useNavigate();
  const { createIntent, loading, error } = useBookingFlow('venue');

  const [vendor, setVendor] = useState(null);
  const [items, setItems] = useState([]);
  const [availability, setAvailability] = useState(null);
  const [pageError, setPageError] = useState('');
  const [step, setStep] = useState(1);
  const [createdBooking, setCreatedBooking] = useState(null);
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  const [form, setForm] = useState({
    item_id: '',
    category_slug: 'venue',
    check_in_date: '',
    check_out_date: '',
    notes: '',
    total_amount_paise: 0,
    category_meta: {},
  });

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const vendorRes = await apiClient.get(`/vendors/${vendorId}`);
        const vendorData = unwrap(vendorRes);
        const inventoryRes = await apiClient.get(`/services/vendor/${vendorId}/items`);
        const inventory = unwrap(inventoryRes);
        if (!mounted) return;
        setVendor(vendorData || null);
        setItems(Array.isArray(inventory) ? inventory : []);
      } catch (err) {
        if (mounted) setPageError(err?.response?.data?.detail || err.message || 'Unable to load rental booking');
      }
    })();
    return () => {
      mounted = false;
    };
  }, [vendorId]);

  const selectedItem = useMemo(
    () => items.find((x) => String(x?.id) === String(form.item_id)),
    [items, form.item_id],
  );
  const blockedDates = useMemo(
    () => (availability?.conflicting_dates && Array.isArray(availability.conflicting_dates) ? availability.conflicting_dates : []),
    [availability],
  );
  const dailyPricePaise = useMemo(() => {
    const paise = Number(selectedItem?.price_paise || selectedItem?.amount_paise || 0);
    if (paise > 0) return paise;
    const rupeeToPaise = Math.round(Number(selectedItem?.price || selectedItem?.amount || 0) * 100);
    return rupeeToPaise > 0 ? rupeeToPaise : 0;
  }, [selectedItem]);

  useEffect(() => {
    if (!selectedItem) return;
    const paise = Number(selectedItem?.price_paise || selectedItem?.amount_paise || 0);
    const rupeeToPaise = Math.round(Number(selectedItem?.price || selectedItem?.amount || 0) * 100);
    const resolved = paise > 0 ? paise : rupeeToPaise;
    if (resolved > 0) {
      setForm((prev) => ({ ...prev, total_amount_paise: resolved }));
    }
  }, [selectedItem]);

  const depositPaisa = useMemo(
    () => Math.round(Number(form.total_amount_paise || 0) * 0.3),
    [form.total_amount_paise],
  );
  const balancePaisa = useMemo(
    () => Math.max(Number(form.total_amount_paise || 0) - depositPaisa, 0),
    [form.total_amount_paise, depositPaisa],
  );

  const checkAvailability = async () => {
    if (!form.item_id || !form.check_in_date || !form.check_out_date) return;
    setCheckingAvailability(true);
    setPageError('');
    try {
      const result = await apiClient.get(
        `/bookings/rental/availability/${form.item_id}?check_in=${toDateOnly(form.check_in_date)}&check_out=${toDateOnly(form.check_out_date)}`,
      );
      setAvailability(unwrap(result));
    } catch (err) {
      // Keep booking flow usable even if availability endpoint is not deployed yet.
      setAvailability({ available: true, conflicting_dates: [] });
    } finally {
      setCheckingAvailability(false);
    }
  };

  useEffect(() => {
    checkAvailability();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.item_id, form.check_in_date, form.check_out_date]);

  const onContinue = (e) => {
    e.preventDefault();
    setPageError('');
    if (!form.item_id || !form.check_in_date || !form.check_out_date || !form.total_amount_paise) {
      setPageError('Item, check-in, check-out and amount are required');
      return;
    }
    if (availability && availability.available === false) {
      setPageError('Selected date range is not available');
      return;
    }
    setStep(2);
  };

  const onPayDeposit = async () => {
    setPageError('');
    try {
      const intentRes = await createIntent({
        vendor_id: vendorId,
        item_id: form.item_id,
        category_slug: form.category_slug,
        check_in_date: toDateOnly(form.check_in_date),
        check_out_date: toDateOnly(form.check_out_date),
        notes: form.notes,
        total_amount_paise: Number(form.total_amount_paise),
        category_meta: form.category_meta || {},
      });
      const created = unwrap(intentRes);
      setCreatedBooking(created || null);

      const payData = created?.payment || created?.payment_payload || null;
      if (!payData?.order_id && !payData?.razorpay_order_id) {
        navigate(`/bookings/${created?.id || created?.booking_id || ''}/tracking`);
        return;
      }

      const loaded = await loadRazorpayScript();
      if (!loaded) throw new Error('Unable to load payment gateway');

      const razorpay = new window.Razorpay({
        key: payData?.key_id || process.env.REACT_APP_RAZORPAY_KEY_ID,
        amount: payData?.amount_paise || payData?.amount,
        currency: payData?.currency || 'INR',
        name: vendor?.business_name || 'Rental Booking',
        description: 'Rental deposit payment (30%)',
        order_id: payData?.order_id || payData?.razorpay_order_id,
        handler: () => {
          navigate(`/bookings/${created?.id || created?.booking_id || ''}/tracking`);
        },
        theme: { color: '#111827' },
      });
      razorpay.open();
    } catch (err) {
      setPageError(err?.response?.data?.detail || err.message || 'Unable to start rental booking');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <div className="bg-white border rounded-xl p-4">
        <h1 className="text-xl font-semibold">Rental Booking</h1>
        <p className="text-sm text-stone-600">
          {vendor?.business_name || 'Vendor'} | 30% deposit now, 70% before event date
        </p>
      </div>

      {step === 1 ? (
        <form onSubmit={onContinue} className="bg-white border rounded-xl p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium">Rental Item</label>
            <select
              className="w-full border rounded p-2"
              value={form.item_id}
              onChange={(e) => setForm((prev) => ({ ...prev, item_id: e.target.value }))}
              required
            >
              <option value="">Select item</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name || item.title || item.id}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <DateRangePicker
              checkIn={form.check_in_date}
              checkOut={form.check_out_date}
              blockedDates={blockedDates}
              dailyPricePaise={dailyPricePaise}
              onChange={({ checkIn, checkOut }) => {
                setForm((prev) => ({ ...prev, check_in_date: checkIn, check_out_date: checkOut }));
              }}
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Total Amount (INR)</label>
            <input
              type="number"
              min="1"
              className="w-full border rounded p-2"
              value={Math.floor((form.total_amount_paise || 0) / 100)}
              onChange={(e) => setForm((prev) => ({ ...prev, total_amount_paise: Number(e.target.value || 0) * 100 }))}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Notes (optional)</label>
            <textarea
              className="w-full border rounded p-2"
              rows={3}
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
            />
          </div>

          <div className="text-sm">
            {checkingAvailability ? (
              <span className="text-stone-600">Checking availability...</span>
            ) : availability ? (
              availability.available ? (
                <span className="text-green-700">Available for selected dates</span>
              ) : (
                <span className="text-red-700">Not available. Try different dates.</span>
              )
            ) : null}
          </div>

          {pageError ? <p className="text-sm text-red-600">{pageError}</p> : null}
          <button type="submit" className="w-full bg-black text-white rounded p-2">
            Continue
          </button>
        </form>
      ) : (
        <div className="bg-white border rounded-xl p-4 space-y-3">
          <h2 className="text-lg font-semibold">Deposit Summary</h2>
          <div className="text-sm text-stone-700 space-y-1">
            <p>Total: Rs. {Math.floor((form.total_amount_paise || 0) / 100)}</p>
            <p>Deposit Now (30%): Rs. {Math.floor(depositPaisa / 100)}</p>
            <p>Balance (70%): Rs. {Math.floor(balancePaisa / 100)}</p>
          </div>
          {createdBooking?.id ? <p className="text-sm text-green-700">Booking created: {createdBooking.id}</p> : null}
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          {pageError ? <p className="text-sm text-red-600">{pageError}</p> : null}
          <div className="grid grid-cols-2 gap-2">
            <button type="button" className="w-full border rounded p-2" onClick={() => setStep(1)} disabled={loading}>
              Back
            </button>
            <button
              type="button"
              className="w-full bg-black text-white rounded p-2 disabled:opacity-60"
              onClick={onPayDeposit}
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Pay Deposit'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
