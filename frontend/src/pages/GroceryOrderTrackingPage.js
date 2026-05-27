import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { groceryApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';

const STATUS_STEPS = ['confirmed', 'processing', 'shipped'];

const GroceryOrderTrackingPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadOrder = async () => {
      setLoading(true);
      try {
        const res = await groceryApi.getOrder(id);
        const payload = res?.data || res;
        const booking = payload?.booking || payload;
        if (booking) {
          const fulfillment = booking?.meta?.fulfillment_status || 'CONFIRMED';
          setOrder({
            id: booking.id,
            status: fulfillment.toLowerCase(),
            items: booking.items || [],
            total_amount: Math.round((booking.amount_gross_paise || 0) / 100),
            delivery_eta: booking?.meta?.tracking_info?.estimated_delivery || 'TBD',
          });
        } else {
          setOrder(null);
        }
      } catch (e) {
        setOrder(null);
      } finally {
        setLoading(false);
      }
    };
    loadOrder();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500">Loading order...</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center bg-white rounded-2xl">
          <p className="text-stone-600">Order not found.</p>
          <Button className="mt-4" onClick={() => navigate('/dashboard')}>Go to Dashboard</Button>
        </Card>
      </div>
    );
  }

  const currentIndex = STATUS_STEPS.indexOf(order.status);

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-4xl mx-auto w-full px-4 md:px-8 py-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-semibold">Grocery Order</h1>
            <p className="text-stone-500">Order ID: {order.id.slice(0, 8)}</p>
          </div>
          <Button variant="outline" onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
        </div>

        <Card className="p-6 bg-white rounded-2xl border border-stone-100 mb-6">
          <h2 className="text-lg font-semibold mb-4">Delivery Progress</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {STATUS_STEPS.map((step, idx) => (
              <div key={step} className={`p-4 rounded-xl border ${idx <= currentIndex ? 'border-emerald-300 bg-emerald-50' : 'border-stone-200 bg-stone-50'}`}>
                <p className="text-sm font-medium text-stone-700">{step.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-stone-500 mt-4">Delivery ETA: {order.delivery_eta}</p>
        </Card>

        <Card className="p-6 bg-white rounded-2xl border border-stone-100">
          <h2 className="text-lg font-semibold mb-4">Items</h2>
          <div className="space-y-2 text-sm text-stone-600">
            {order.items.map((item) => (
              <div key={item.item_id} className="flex items-center justify-between">
                <span>{item.title || item.name} x {item.qty}</span>
                <span>₹{Math.round((item.total_price_paise || 0) / 100).toLocaleString()}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-stone-200 mt-4 pt-4 flex items-center justify-between font-semibold">
            <span>Total</span>
            <span>₹{order.total_amount.toLocaleString()}</span>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default GroceryOrderTrackingPage;
