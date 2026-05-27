import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useGroceryCart } from '../contexts/GroceryCartContext';
import apiClient from '../lib/apiClient';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import ReservationTimer from '../components/grocery/ReservationTimer';

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

const DEFAULT_ADDRESS = {
  name: '',
  phone: '',
  line1: '',
  line2: '',
  city: '',
  state: '',
  postal_code: '',
  instructions: '',
};

export default function GroceryCheckoutPage() {
  const navigate = useNavigate();
  const { cart, subtotal, clearCart } = useGroceryCart();

  const [address, setAddress] = useState(DEFAULT_ADDRESS);
  const [lockState, setLockState] = useState(null); // {lock_id, expires_at, total_amount_paise, items}
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [reserving, setReserving] = useState(false);
  const [paying, setPaying] = useState(false);
  const [releasing, setReleasing] = useState(false);
  const [expiryHandled, setExpiryHandled] = useState(false);

  const expired = timerSeconds === 0 && !!lockState?.lock_id;

  const cartItemsPayload = useMemo(
    () => cart.items.map((item) => ({ item_id: item.item_id, qty: item.qty })),
    [cart.items],
  );

  useEffect(() => {
    if (!cart.items.length) navigate('/grocery/cart');
  }, [cart.items.length, navigate]);

  useEffect(() => {
    if (!lockState?.expires_at) return undefined;
    const tick = () => {
      const expiryMs = new Date(lockState.expires_at).getTime();
      const nowMs = Date.now();
      const left = Math.max(0, Math.floor((expiryMs - nowMs) / 1000));
      setTimerSeconds(left);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [lockState?.expires_at]);

  useEffect(() => {
    if (!expired || expiryHandled) return;
    setExpiryHandled(true);
    (async () => {
      try {
        if (lockState?.lock_id) {
          await apiClient.del(`/grocery/cart/reserve/${lockState.lock_id}`);
        }
      } catch {
        // no-op: lock may already be released server-side
      } finally {
        setLockState(null);
      }
    })();
    toast.error('Time expired - items released');
  }, [expired, expiryHandled, lockState?.lock_id]);

  const reserveCart = async () => {
    if (!cart.vendorId || !cart.items.length) return;
    setReserving(true);
    try {
      const res = await apiClient.post('/grocery/cart/reserve', {
        vendor_id: cart.vendorId,
        items: cartItemsPayload,
      });
      const data = unwrap(res);
      setLockState(data);
      setExpiryHandled(false);
      toast.success('Stock reserved for 15 minutes');
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || 'Failed to reserve stock');
    } finally {
      setReserving(false);
    }
  };

  useEffect(() => {
    if (!cart.vendorId || !cart.items.length) return;
    reserveCart();
    // reserve once on current checkout cart snapshot
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart.vendorId, JSON.stringify(cartItemsPayload)]);

  const releaseLock = async () => {
    if (!lockState?.lock_id) return;
    setReleasing(true);
    try {
      await apiClient.del(`/grocery/cart/reserve/${lockState.lock_id}`);
      setLockState(null);
      toast.success('Reserved stock released');
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || 'Unable to release lock');
    } finally {
      setReleasing(false);
    }
  };

  const phoneDigits = (address.phone || '').replace(/\D/g, '');
  const validAddress =
    address.name &&
    phoneDigits.length === 10 &&
    address.line1 &&
    address.city &&
    address.state &&
    /^[0-9]{6}$/.test(String(address.postal_code || '').trim());

  const verifyPayment = async (payload) => {
    try {
      const res = await apiClient.post('/bookings/verify', payload);
      return unwrap(res);
    } catch (err) {
      throw new Error(err?.response?.data?.detail || err.message || 'Payment verification failed');
    }
  };

  const handlePay = async () => {
    if (!lockState?.lock_id) {
      toast.error('No active reservation found');
      return;
    }
    if (timerSeconds <= 0) {
      toast.error('Lock expired. Reserve cart again.');
      return;
    }
    if (!validAddress) {
      toast.error('Please complete valid address (10-digit phone, 6-digit pincode)');
      return;
    }

    setPaying(true);
    try {
      const idempotency = `grocery_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
      const checkoutRes = await apiClient.post('/grocery/checkout', {
        lock_id: lockState.lock_id,
        idempotency_key: idempotency,
        delivery_address: `${address.line1}, ${address.city}, ${address.state} ${address.postal_code}`,
        notes: address.instructions,
      });
      const checkout = unwrap(checkoutRes);
      const orderId = checkout?.razorpay_order_id;
      const amount = checkout?.amount_paise;
      const key = checkout?.key_id;
      const intentId = checkout?.booking_intent_id;
      if (!orderId || !amount || !key || !intentId) {
        throw new Error('Invalid checkout response');
      }

      const sdkLoaded = await loadRazorpayScript();
      if (!sdkLoaded) throw new Error('Unable to load payment gateway');

      const razorpay = new window.Razorpay({
        key,
        amount,
        currency: checkout?.currency || 'INR',
        name: 'Grocery Checkout',
        description: 'Wholesale grocery order',
        order_id: orderId,
        handler: async (resp) => {
          try {
            const verified = await verifyPayment({
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
              booking_intent_id: intentId,
            });
            clearCart();
            toast.success('Payment successful');
            navigate(`/grocery/orders/${verified?.booking_id || verified?.order_id || intentId}`);
          } catch (e) {
            toast.error(e.message || 'Payment verify failed');
          }
        },
        theme: { color: '#111827' },
      });
      razorpay.open();
    } catch (err) {
      toast.error(err?.message || err?.response?.data?.detail || 'Checkout failed');
    } finally {
      setPaying(false);
    }
  };

  if (!cart.items.length) return null;
  const totalDisplay = lockState?.total_amount_paise ? lockState.total_amount_paise / 100 : Number(subtotal || 0);

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-5xl mx-auto w-full px-4 md:px-8 py-10">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold">Grocery Checkout</h1>
          <p className="text-stone-500">Reserve stock for 15 minutes and complete payment.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[1fr_340px] gap-6">
          <Card className="p-6 bg-white rounded-2xl border border-stone-100">
            <h2 className="text-lg font-semibold mb-4">Delivery Address</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input placeholder="Full Name" value={address.name} onChange={(e) => setAddress({ ...address, name: e.target.value })} />
              <Input placeholder="Phone" value={address.phone} onChange={(e) => setAddress({ ...address, phone: e.target.value })} />
              <Input placeholder="Address Line 1" value={address.line1} onChange={(e) => setAddress({ ...address, line1: e.target.value })} />
              <Input placeholder="Address Line 2" value={address.line2} onChange={(e) => setAddress({ ...address, line2: e.target.value })} />
              <Input placeholder="City" value={address.city} onChange={(e) => setAddress({ ...address, city: e.target.value })} />
              <Input placeholder="State" value={address.state} onChange={(e) => setAddress({ ...address, state: e.target.value })} />
              <Input placeholder="Postal Code" value={address.postal_code} onChange={(e) => setAddress({ ...address, postal_code: e.target.value })} />
              <Input
                placeholder="Landmark / Delivery Instructions"
                value={address.instructions}
                onChange={(e) => setAddress({ ...address, instructions: e.target.value })}
              />
            </div>
          </Card>

          <Card className="p-6 bg-white rounded-2xl border border-stone-100 h-fit">
            <h2 className="text-lg font-semibold mb-3">Order Summary</h2>
            <div className="space-y-2 text-sm text-stone-600">
              {cart.items.map((item) => (
                <div key={item.item_id} className="flex items-center justify-between">
                  <span>{item.name} x {item.qty}</span>
                  <span>Rs. {Number(item.total_price || 0).toLocaleString()}</span>
                </div>
              ))}
            </div>
            <div className="border-t border-stone-200 mt-4 pt-4 flex items-center justify-between font-semibold">
              <span>Total</span>
              <span>Rs. {Number(totalDisplay || 0).toLocaleString()}</span>
            </div>

            <div className="mt-4">
              {lockState?.lock_id ? (
                <ReservationTimer expiresAt={lockState?.expires_at} onExpire={() => toast.error('Time expired - items released')} />
              ) : (
                <div className="rounded-lg border border-stone-200 bg-stone-50 p-3 text-sm text-stone-500">No active reservation</div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2 mt-4">
              <Button variant="outline" onClick={reserveCart} disabled={reserving || paying}>
                {reserving ? 'Reserving...' : 'Reserve Again'}
              </Button>
              <Button variant="outline" onClick={releaseLock} disabled={releasing || paying || !lockState?.lock_id}>
                {releasing ? 'Releasing...' : 'Release Lock'}
              </Button>
            </div>

            <Button className="w-full mt-4" onClick={handlePay} disabled={paying || reserving || !lockState?.lock_id || timerSeconds <= 0}>
              {paying ? 'Processing...' : 'Pay Now'}
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
