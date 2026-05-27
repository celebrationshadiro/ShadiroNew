import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../lib/apiClient';
import BookingTimeline from '../components/BookingTimeline';

export default function BookingTrackingPage() {
  const { bookingId } = useParams();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const res = await apiClient.get(`/bookings/${bookingId}`);
        const data = res && res.data ? res.data : res;
        if (mounted) setBooking(data);
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || err.message || 'Unable to load booking');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [bookingId]);

  if (loading) return <div className="max-w-xl mx-auto p-4">Loading booking...</div>;
  if (error) return <div className="max-w-xl mx-auto p-4 text-red-600">{error}</div>;
  if (!booking) return null;

  return (
    <div className="max-w-xl mx-auto p-4 space-y-4">
      <div className="bg-white rounded border p-4">
        <h1 className="text-lg font-semibold">Booking #{booking.id}</h1>
        <p className="text-sm text-stone-600">Status: {booking.status}</p>
      </div>
      <div className="bg-white rounded border p-4">
        <BookingTimeline categoryType={booking.category_type} status={booking.status} />
      </div>
    </div>
  );
}
