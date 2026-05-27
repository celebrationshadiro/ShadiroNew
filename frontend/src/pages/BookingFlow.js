import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { CategoryServiceSelector } from '../components/CategoryServiceSelector';
import apiClient from '../lib/apiClient';
import { bookingFlowsApi, vendors as vendorsApi, payments as paymentsApi } from '../lib/api';
import { toast } from 'sonner';
import '../styles/BookingFlow.css';

const BookingFlow = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { vendorId } = useParams();
  const { user } = useAuth();

  const [vendor, setVendor] = useState(null);
  const [flowTemplate, setFlowTemplate] = useState(null);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [bookingId, setBookingId] = useState(null);
  const [selectedServices, setSelectedServices] = useState(location.state?.selectedServices || []);
  const [categoryQuickDetails, setCategoryQuickDetails] = useState({});
  const [paymentMethod, setPaymentMethod] = useState('upi');

  const [bookingDetails, setBookingDetails] = useState({
    event_date: '',
    start_time: '',
    end_time: '',
    event_city: '',
    event_location: '',
    additional_notes: '',
    preferred_contact: 'whatsapp',
  });

  useEffect(() => {
    const loadVendorAndFlow = async () => {
      try {
        const vendorRes = await vendorsApi.getById(vendorId);
        const vendorData = vendorRes?.data || null;
        setVendor(vendorData);

        const flowRes = await bookingFlowsApi.getByVendor(vendorId);
        setFlowTemplate(flowRes?.data || null);
      } catch (err) {
        console.error('Failed to load booking context:', err);
      }
    };
    if (vendorId) loadVendorAndFlow();
  }, [vendorId]);

  useEffect(() => {
    setBookingDetails((prev) => {
      const next = { ...prev };
      Object.entries(categoryQuickDetails || {}).forEach(([key, value]) => {
        if (next[key] === '' || next[key] === undefined || next[key] === null) {
          next[key] = value;
        }
      });
      return next;
    });
  }, [categoryQuickDetails]);

  const priceBreakdown = useMemo(() => {
    const subtotal = selectedServices.reduce((sum, service) => {
      const qty = service.quantity || service.qty || 1;
      const unitPrice = service.unit_price || service.price || 0;
      return sum + (unitPrice * qty);
    }, 0);
    const tax = Math.round(subtotal * 0.18);
    const fee = subtotal > 0 ? 99 : 0;
    const total = subtotal + tax + fee;
    const advancePct = Number(flowTemplate?.advance_percentage || 30);
    const advanceAmount = Math.round((total * advancePct) / 100);
    return { subtotal, tax, fee, total, advancePct, advanceAmount };
  }, [selectedServices, flowTemplate]);

  const bookingInputs = flowTemplate?.booking_inputs?.length
    ? flowTemplate.booking_inputs
    : [
        { key: 'event_date', label: 'Event Date', type: 'date', required: true },
        { key: 'start_time', label: 'Start Time', type: 'time', required: true },
        { key: 'event_city', label: 'City', type: 'text', required: true },
        { key: 'event_location', label: 'Venue / Locality', type: 'text', required: true },
      ];

  const setField = (key, value) => {
    setBookingDetails((prev) => ({ ...prev, [key]: value }));
  };

  const validateStepTwo = () => {
    for (const field of bookingInputs) {
      if (!field.required) continue;
      const value = bookingDetails[field.key] ?? categoryQuickDetails[field.key];
      if (value === undefined || value === null || String(value).trim() === '') {
        toast.error(`Please enter ${field.label}`);
        return false;
      }
    }
    return true;
  };

  const handleNextStep = () => {
    if (step === 1 && selectedServices.length === 0) {
      toast.error('Please select at least one service');
      return;
    }
    if (step === 2 && !validateStepTwo()) return;
    setStep((s) => s + 1);
  };

  const handleConfirmBooking = async () => {
    if (!user) {
      toast.error('Please login first');
      navigate('/auth');
      return;
    }

    setLoading(true);
    try {
      const items = selectedServices.map((service) => {
        const qty = service.quantity || service.qty || 1;
        const unitPriceRupee = service.unit_price || service.price || 0;
        const unitPricePaise = Math.round(unitPriceRupee * 100);
        return {
          item_id: service.id || service.item_id || service.name || `item_${Math.random().toString(36).slice(2, 8)}`,
          title: service.name || service.title || 'Service',
          qty,
          unit_price_paise: unitPricePaise,
          total_price_paise: unitPricePaise * qty,
          meta: { unit: service.unit || 'item' },
        };
      });
      const totalPaise = Math.round(priceBreakdown.total * 100);
      const payload = {
        idempotency_key: `intent_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        user_id: user.id,
        vendor_id: vendorId,
        category_type: 'service',
        items,
        total_amount_paise: totalPaise,
        scheduled_at: bookingDetails.event_date ? `${bookingDetails.event_date}T${bookingDetails.start_time || '00:00'}:00+05:30` : null,
        duration_minutes: null,
        notes: bookingDetails.additional_notes || null,
        meta: {
          location: bookingDetails.event_location,
          event_city: bookingDetails.event_city,
          event_date: bookingDetails.event_date,
          start_time: bookingDetails.start_time,
          end_time: bookingDetails.end_time || null,
          category_id: flowTemplate?.category_id || vendor?.category_id || null,
          category_flow_version: flowTemplate?.flow_version || 'generic',
          category_booking_details: {
            ...categoryQuickDetails,
            ...bookingDetails,
            preferred_contact: bookingDetails.preferred_contact,
          },
        },
      };

      const data = await apiClient.post('/bookings/intent', payload);
      const created = data?.data || data;
      const intentId = created?.id || created?.booking_intent_id || null;
      if (!intentId) {
        throw new Error('Booking intent ID missing from response');
      }

      const payRes = await paymentsApi.createOrder(intentId);
      const payData = payRes?.data || {};
      const orderId = payData?.razorpay_order_id;
      const amount = payData?.amount_paise || payData?.amount;
      const key = payData?.key_id;
      if (!orderId || !amount || !key) {
        throw new Error('Invalid payment order response');
      }

      const sdkLoaded = await loadRazorpay();
      if (!sdkLoaded) {
        throw new Error('Razorpay SDK failed to load');
      }

      const razorpay = new window.Razorpay({
        key,
        amount,
        currency: payData?.currency || 'INR',
        name: 'Shadiro',
        description: `Booking for ${vendor?.business_name || 'Event Services'}`,
        order_id: orderId,
        prefill: {
          name: user?.name || '',
          email: user?.email || '',
          contact: user?.phone || '',
        },
        handler: async (response) => {
          try {
            const verifyRes = await paymentsApi.verify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              booking_intent_id: intentId,
            });
            const verified = verifyRes?.data || verifyRes;
            const confirmedBookingId = verified?.booking_id || intentId;
            setBookingId(confirmedBookingId);
            toast.success('Payment successful! Booking confirmed.');
            setStep(5);
          } catch (verifyErr) {
            console.error('Payment verification failed:', verifyErr);
            toast.error(verifyErr?.response?.data?.detail || 'Payment verification failed');
          }
        },
      });

      razorpay.on('payment.failed', () => {
        toast.error('Payment failed. Please try again.');
      });
      razorpay.open();
    } catch (error) {
      console.error('Error creating booking:', error);
      toast.error(error?.response?.data?.detail || error.message || 'Please try again');
    } finally {
      setLoading(false);
    }
  };

  const loadRazorpay = () => {
    return new Promise((resolve) => {
      if (window.Razorpay) return resolve(true);
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const renderInputField = (field) => {
    const value = bookingDetails[field.key] ?? categoryQuickDetails[field.key] ?? '';
    const common = {
      value,
      required: !!field.required,
      onChange: (e) => setField(field.key, e.target.value),
    };

    return (
      <div className="form-group" key={field.key}>
        <label>{field.label}{field.required ? ' *' : ''}</label>
        {field.type === 'number' ? (
          <input type="number" min="0" {...common} />
        ) : (
          <input type={field.type || 'text'} {...common} />
        )}
      </div>
    );
  };

  if (step === 1) {
    return (
      <div className="booking-flow">
        <div className="flow-container">
          <h2>Step 1: Select Services</h2>
          {vendor?.category_id && (
            <CategoryServiceSelector
              vendorId={vendorId}
              categoryId={vendor.category_id}
              onSelectionChange={setSelectedServices}
              onMetaChange={setCategoryQuickDetails}
            />
          )}
          <div className="button-group">
            <Button onClick={() => navigate(-1)} variant="secondary">Back</Button>
            <Button onClick={handleNextStep} disabled={selectedServices.length === 0}>Continue</Button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 2) {
    return (
      <div className="booking-flow">
        <div className="flow-container">
          <h2>Step 2: Event Details</h2>
          <form>
            {bookingInputs.map(renderInputField)}
            <div className="form-group">
              <label>Preferred Contact</label>
              <select
                value={bookingDetails.preferred_contact}
                onChange={(e) => setField('preferred_contact', e.target.value)}
              >
                <option value="whatsapp">WhatsApp</option>
                <option value="call">Call</option>
                <option value="email">Email</option>
              </select>
            </div>
            <div className="form-group">
              <label>Additional Notes</label>
              <textarea
                value={bookingDetails.additional_notes}
                onChange={(e) => setField('additional_notes', e.target.value)}
                placeholder="Optional notes for vendor"
              />
            </div>
          </form>
          <div className="button-group">
            <Button onClick={() => setStep(1)} variant="secondary">Back</Button>
            <Button onClick={handleNextStep}>Continue</Button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="booking-flow">
        <div className="flow-container">
          <h2>Step 3: Review & Pay Advance</h2>
          <Card className="summary-card">
            <h3>Summary</h3>
            <div className="price-breakdown">
              <div className="breakdown-row"><span>Subtotal:</span><span>Rs. {priceBreakdown.subtotal}</span></div>
              <div className="breakdown-row"><span>Tax (18%):</span><span>Rs. {priceBreakdown.tax}</span></div>
              <div className="breakdown-row"><span>Platform Fee:</span><span>Rs. {priceBreakdown.fee}</span></div>
              <div className="breakdown-row total"><span>Total:</span><span>Rs. {priceBreakdown.total}</span></div>
              <div className="breakdown-row total">
                <span>Pay Now ({priceBreakdown.advancePct}%):</span>
                <span>Rs. {priceBreakdown.advanceAmount}</span>
              </div>
            </div>
          </Card>
          <Card className="payment-card">
            <h3>Payment Method</h3>
            <div className="payment-options">
              {['upi', 'card', 'wallet'].map((method) => (
                <label key={method}>
                  <input
                    type="radio"
                    value={method}
                    checked={paymentMethod === method}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                  />
                  {method.toUpperCase()}
                </label>
              ))}
            </div>
          </Card>
          <div className="button-group">
            <Button onClick={() => setStep(2)} variant="secondary">Back</Button>
            <Button onClick={handleConfirmBooking} loading={loading}>Confirm Booking</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="booking-flow">
      <div className="confirmation-container">
        <h1>Booking Confirmed</h1>
        <p>Your booking has been placed successfully.</p>
        <Card className="confirmation-details">
          <div className="detail-row"><span>Booking ID:</span><strong>#{bookingId}</strong></div>
          <div className="detail-row"><span>Total:</span><strong>Rs. {priceBreakdown.total}</strong></div>
        </Card>
        <div className="button-group">
          <Button onClick={() => navigate('/bookings')}>View My Bookings</Button>
          <Button onClick={() => navigate('/')} variant="secondary">Go Home</Button>
        </div>
      </div>
    </div>
  );
};

export default BookingFlow;
