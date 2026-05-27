import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ServiceBookingForm from '../components/service/ServiceBookingForm';
import GroceryCheckoutForm from '../components/grocery/GroceryCheckoutForm';
import RentalBookingForm from '../components/rental/RentalBookingForm';
import useDynamicBooking from '../hooks/useDynamicBooking';

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function DynamicBookingPage() {
  const { vendorId } = useParams();
  const navigate = useNavigate();
  const { vendor, categoryType, loading, error, createIntent, createOrder, verifyPayment } = useDynamicBooking(vendorId);
  const [submitting, setSubmitting] = useState(false);
  const [flowError, setFlowError] = useState('');

  const FormComponent = useMemo(() => {
    if (categoryType === 'grocery') return GroceryCheckoutForm;
    if (categoryType === 'rental') return RentalBookingForm;
    return ServiceBookingForm;
  }, [categoryType]);

  useEffect(() => {
    if (loading || !vendorId) return;
    if (categoryType === 'service') {
      navigate(`/book/${vendorId}/service`, { replace: true });
      return;
    }
    if (categoryType === 'rental') {
      navigate(`/book/${vendorId}/rental`, { replace: true });
      return;
    }
    if (categoryType === 'grocery') {
      navigate(`/vendors/${vendorId}`, { replace: true });
    }
  }, [categoryType, loading, navigate, vendorId]);

  const handleSubmit = async (payload) => {
    setSubmitting(true);
    setFlowError('');
    try {
      const intent = await createIntent(payload);
      const order = await createOrder(intent.intent_id);

      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        throw new Error('Razorpay SDK failed to load');
      }

      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: vendor?.business_name || 'Booking Payment',
        description: 'Booking token payment',
        order_id: order.order_id,
        handler: async function (response) {
          const verifyRes = await verifyPayment({
            intent_id: intent.intent_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          navigate(`/bookings/${verifyRes.booking_id}/tracking`);
        },
        theme: { color: '#111827' },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (err) {
      setFlowError(err?.response?.data?.detail || err.message || 'Booking failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="max-w-xl mx-auto p-4">Loading vendor...</div>;
  if (error) return <div className="max-w-xl mx-auto p-4 text-red-600">{error}</div>;

  return (
    <div className="max-w-xl mx-auto p-4 space-y-4">
      <div className="bg-white rounded border p-4">
        <h1 className="text-xl font-semibold">Book {vendor?.business_name}</h1>
        <p className="text-sm text-stone-600">Category flow: {categoryType}</p>
      </div>
      <div className="bg-white rounded border p-4">
        <FormComponent onSubmit={handleSubmit} loading={submitting} />
      </div>
      {flowError ? <div className="text-sm text-red-600">{flowError}</div> : null}
    </div>
  );
}
