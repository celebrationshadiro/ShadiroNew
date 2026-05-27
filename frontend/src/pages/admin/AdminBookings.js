import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { admin } from '../../lib/api';
import CategoryBadge from '../../components/CategoryBadge';
import { AlertTriangle, Calendar, Loader2, MapPin, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';

const statusColors = {
  pending: 'bg-amber-100 text-amber-800',
  confirmed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
  completed: 'bg-blue-100 text-blue-800',
};

const extractPayload = (response) => response?.data?.data ?? response?.data ?? response;
const extractList = (response) => {
  const payload = extractPayload(response);
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.bookings)) return payload.bookings;
  if (Array.isArray(payload?.emergencies)) return payload.emergencies;
  return [];
};

const AdminBookings = () => {
  const [bookings, setBookings] = useState([]);
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      const [res, emerg] = await Promise.all([
        admin.getBookings({ limit: 100 }),
        admin.getEmergencyBookings({ limit: 50 }),
      ]);
      setBookings(extractList(res));
      setEmergencies(extractList(emerg));
    } catch (err) {
      console.error('Failed to load bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReplacement = async (bookingId) => {
    try {
      await admin.approveEmergencyReplacement(bookingId);
      toast.success('Replacement approved');
      loadBookings();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve replacement');
    }
  };

  const handleRefund = async (bookingId) => {
    try {
      await admin.initiateEmergencyRefund(bookingId);
      toast.success('Refund initiated');
      loadBookings();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to initiate refund');
    }
  };

  const handleEscalate = async (bookingId) => {
    try {
      await admin.escalateEmergency(bookingId, 'Manual review');
      toast.success('Escalated to manual review');
      loadBookings();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to escalate');
    }
  };

  const serviceBookings = (Array.isArray(bookings) ? bookings : []).filter((b) => {
    const context = String(b.booking_context || b.vendor_type || b.type || '').toLowerCase();
    return context !== 'grocery';
  });

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Service Bookings</h1>

      {emergencies.length > 0 && (
        <Card className="mb-6 p-5 border border-amber-200 bg-amber-50">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="text-amber-600" size={18} />
            <p className="text-sm font-semibold text-amber-900">Emergency Cancellations</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {emergencies.map((e) => (
              <Card key={e.id || e.booking_id} className="p-4 border border-amber-200 bg-white shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <CategoryBadge category={e.vendor_category} />
                    <Badge variant="outline" className="text-red-600 border-red-200">Emergency</Badge>
                  </div>
                  {e.impact_score && (
                    <span className="text-sm font-semibold text-red-700">Impact {e.impact_score}</span>
                  )}
                </div>
                <p className="text-sm text-stone-700 mb-1">{e.vendor_name}</p>
                <p className="text-xs text-stone-500 mb-2">Reason: {e.reason}</p>
                <p className="text-xs text-stone-500 mb-1">Event: {e.event_location || '—'}</p>
                <p className="text-xs text-stone-500 mb-3">Booking ID: {e.id || e.booking_id}</p>
                <div className="flex gap-2 flex-wrap">
                  <Button size="sm" onClick={() => handleApproveReplacement(e.id || e.booking_id)} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                    Approve Replacement
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleRefund(e.id || e.booking_id)}>
                    Refund
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => handleEscalate(e.id || e.booking_id)}>
                    Escalate
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </Card>
      )}
      {loading ? (
        <div className="flex items-center gap-2 text-stone-500">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading bookings...
        </div>
      ) : serviceBookings.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-stone-500">No service bookings available.</p>
        </Card>
      ) : (
        <div className="space-y-3 overflow-x-auto">
          {serviceBookings.map((o) => (
            <Card key={o.id} className="p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div className="flex items-center gap-3">
                <CategoryBadge slug={o.vendor_category || o.category_slug} />
                <div>
                  <h3 className="font-medium">Booking #{(o.id || '').slice(0, 8)}</h3>
                  <p className="text-sm text-stone-500">₹{o.total_amount?.toLocaleString() || '—'}</p>
                  <p className="text-xs text-stone-500">Context: {o.booking_context || 'SERVICE'} • Venue: {o.venue_type || 'not set'}</p>
                </div>
              </div>
              <div className="text-sm text-stone-600 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {o.event_date || 'Date not set'}
              </div>
              <div className="text-sm text-stone-600 flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                {o.event_location || o.location || o.event_city || 'Event location not set'}
              </div>
              <div className="flex items-center gap-2">
                <Badge className={statusColors[o.status] || 'bg-stone-100 text-stone-700'}>{o.status || 'pending'}</Badge>
                {o.cancellation_risk && (
                  <Badge className="bg-red-100 text-red-700 flex items-center gap-1">
                    <AlertTriangle size={12} /> Risk
                  </Badge>
                )}
                {o.dispute || o.dispute_indicator ? (
                  <Badge className="bg-amber-100 text-amber-700">Dispute</Badge>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminBookings;
