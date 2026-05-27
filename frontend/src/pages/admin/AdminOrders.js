import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { groceryApi } from '../../lib/api';
import { Loader2, PackageCheck, Truck, RotateCcw, AlertTriangle, MapPin } from 'lucide-react';

const statusColor = (status) => {
  switch ((status || '').toLowerCase()) {
    case 'packed': return 'bg-blue-100 text-blue-800';
    case 'out_for_delivery': return 'bg-amber-100 text-amber-800';
    case 'delivered': return 'bg-green-100 text-green-800';
    case 'cancelled': return 'bg-red-100 text-red-800';
    default: return 'bg-stone-100 text-stone-700';
  }
};

const AdminOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const res = await groceryApi.listOrders({});
      setOrders(res.data || []);
    } catch (err) {
      console.error('Failed to load grocery orders:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Grocery Orders</h1>
      {loading ? (
        <div className="flex items-center gap-2 text-stone-500">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading orders...
        </div>
      ) : orders.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-stone-500">No grocery orders available.</p>
        </Card>
      ) : (
        <div className="space-y-3 overflow-x-auto">
          {orders.map((o) => (
            <Card key={o.id} className="p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div>
                <h3 className="font-medium">Order #{(o.id || '').slice(0, 8)}</h3>
                <p className="text-sm text-stone-500">
                  Items: {o.items?.length || 0} • Amount: ₹{o.total_amount?.toLocaleString?.() || o.total_amount}
                </p>
                <p className="text-xs text-stone-500 mt-1 flex items-center gap-1">
                  <MapPin size={12} /> {o.delivery_zone || o.delivery_address?.city || '—'}
                </p>
                {o.serviceability_warning && (
                  <p className="text-xs text-amber-700 mt-1 flex items-center gap-1">
                    <AlertTriangle size={12} /> {o.serviceability_warning === 'city_mismatch' ? 'City mismatch' : 'Out of zone'}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge className={statusColor(o.status)}>{o.status}</Badge>
                {o.payment_status && (
                  <Badge variant="outline" className="text-green-700 border-green-200 bg-green-50">
                    {o.payment_status}
                  </Badge>
                )}
                {o.refund_flag && (
                  <Badge variant="outline" className="text-red-700 border-red-200 bg-red-50">
                    Refund flagged
                  </Badge>
                )}
                {o.stock_issue && (
                  <Badge variant="outline" className="text-amber-700 border-amber-200 bg-amber-50">
                    Stock issue
                  </Badge>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminOrders;
