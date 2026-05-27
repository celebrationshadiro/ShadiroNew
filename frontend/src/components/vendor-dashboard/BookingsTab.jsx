import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Package, AlertTriangle } from 'lucide-react';

const normalizeBookingStatus = (raw) => String(raw || '').toUpperCase();

const BookingsTab = ({
  bookings,
  pendingBookings,
  confirmedBookings,
  onAccept,
  onReject,
  onEmergencyCancel,
  navigate,
}) => (
  <>
    <h2 className="text-2xl font-semibold mb-6">Booking Management</h2>
    {bookings.length === 0 ? (
      <Card className="p-12 text-center bg-white rounded-2xl">
        <Package className="mx-auto mb-4 text-stone-300" size={48} />
        <p className="text-stone-500 mb-4">No bookings yet</p>
      </Card>
    ) : (
      <div className="space-y-4">
        {pendingBookings.length > 0 && (
          <>
            <h3 className="text-xl font-semibold text-amber-700 mt-6 mb-3">⏳ Pending Bookings</h3>
            {pendingBookings.map((booking) => (
              <Card key={booking.id} className="p-6 bg-white rounded-2xl border-l-4 border-l-amber-400">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{booking.user_name}</h3>
                    <p className="text-sm text-stone-500">Booking #{booking.id}</p>
                  </div>
                  <span className="text-2xl font-bold text-primary">₹{booking.total_amount?.toLocaleString()}</span>
                </div>
                <p className="text-stone-600 mb-2">📅 {booking.event_date} @ {booking.event_time}</p>
                <p className="text-stone-600 mb-4">📍 {booking.address}</p>
                <div className="flex gap-2 flex-wrap">
                  <Button onClick={() => onAccept(booking.id)} className="bg-green-600 hover:bg-green-700 rounded-lg">✓ Accept Booking</Button>
                  <Button onClick={() => onReject(booking.id)} variant="outline" className="rounded-lg">✗ Reject</Button>
                  <Button onClick={() => navigate(`/chat/${booking.user_id}`)} variant="outline" className="rounded-lg">💬 Chat</Button>
                </div>
              </Card>
            ))}
          </>
        )}

        {confirmedBookings.length > 0 && (
          <>
            <h3 className="text-xl font-semibold text-green-700 mt-8 mb-3">✅ Confirmed Bookings</h3>
            {confirmedBookings.map((booking) => (
              <Card key={booking.id} className="p-6 bg-white rounded-2xl border-l-4 border-l-green-400">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{booking.user_name}</h3>
                    <p className="text-sm text-stone-500">Booking #{booking.id}</p>
                  </div>
                  <span className="text-2xl font-bold text-green-600">₹{booking.total_amount?.toLocaleString()}</span>
                </div>
                <p className="text-stone-600 mb-2">📅 {booking.event_date} @ {booking.event_time}</p>
                <p className="text-stone-600 mb-4">📍 {booking.address}</p>
                <div className="flex gap-2">
                  <Button onClick={() => navigate(`/chat/${booking.user_id}`)} variant="outline" className="rounded-lg">💬 Chat</Button>
                  <Button onClick={() => onEmergencyCancel(booking.id)} className="bg-red-600 hover:bg-red-700 rounded-lg">
                    <AlertTriangle size={16} className="mr-2" /> Emergency Cancel
                  </Button>
                </div>
              </Card>
            ))}
          </>
        )}
      </div>
    )}
  </>
);

export default BookingsTab;
