import React, { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Calendar, MapPin, Clock, MessageSquare, AlertCircle, Check, X } from 'lucide-react';

/**
 * BookingCard Component
 * 
 * Displays booking status and details with:
 * - Vendor info (name, image, rating)
 * - Service details (event date, time, location)
 * - Booking status (confirmed, pending, cancelled, completed)
 * - Status badges
 * - Quick actions (chat, reschedule, cancel, pay)
 * - Countdown timer for upcoming events
 * - Responsive design
 * 
 * @component
 * @example
 * <BookingCard
 *   booking={bookingData}
 *   onChat={handleChat}
 *   onReschedule={handleReschedule}
 *   onCancel={handleCancel}
 * />
 */

export const BookingCard = ({
  booking = {},
  onChat,
  onReschedule,
  onCancel,
  onRate,
  onPay,
  className,
}) => {
  const [showActions, setShowActions] = useState(false);

  // Default booking data
  const bookingData = {
    id: booking.id || '1',
    vendorName: booking.vendorName || 'Premium Photography Studio',
    vendorImage: booking.vendorImage || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=100&h=100&fit=crop',
    vendorRating: booking.vendorRating || 4.8,
    serviceName: booking.serviceName || 'Wedding Photography',
    serviceCategory: booking.serviceCategory || 'Photography',
    eventDate: booking.eventDate || '2024-05-15',
    eventTime: booking.eventTime || '10:00 AM - 6:00 PM',
    eventLocation: booking.eventLocation || 'The Grand Ballroom, Mumbai',
    status: booking.status || 'confirmed', // confirmed, pending, completed, cancelled, emergency
    amount: booking.amount || 75000,
    currency: booking.currency || '₹',
    paymentStatus: booking.paymentStatus || 'paid', // paid, pending, refunded
    daysUntil: booking.daysUntil || 32,
    bookingId: booking.bookingId || 'BK-2024-001234',
    replacementSuggestions: booking.replacementSuggestions || booking.replacement_suggestions || [],
  };

  // Status styling configuration
  const statusConfig = {
    confirmed: {
      color: 'bg-success/10 text-success',
      icon: Check,
      label: 'Confirmed',
      actions: ['chat', 'reschedule', 'countdown'],
    },
    pending: {
      color: 'bg-warning/10 text-warning',
      icon: Clock,
      label: 'Awaiting Confirmation',
      actions: ['chat', 'cancel'],
    },
    completed: {
      color: 'bg-info/10 text-info',
      icon: Check,
      label: 'Event Completed',
      actions: ['chat', 'download', 'rate'],
    },
    cancelled: {
      color: 'bg-error/10 text-error',
      icon: X,
      label: 'Cancelled',
      actions: ['chat'], // Refund info might be shown
    },
    vendor_cancelled: {
      color: 'bg-error/10 text-error',
      icon: X,
      label: 'Vendor Cancelled',
      actions: ['chat', 'details'],
    },
    cancelled_by_vendor: {
      color: 'bg-error/10 text-error',
      icon: X,
      label: 'Vendor Cancelled',
      actions: ['chat', 'details'],
    },
    vendor_cancelled_emergency: {
      color: 'bg-error/10 text-error',
      icon: AlertCircle,
      label: 'Vendor Emergency',
      actions: ['chat', 'details'],
    },
    cancelled_by_vendor_emergency: {
      color: 'bg-error/10 text-error',
      icon: AlertCircle,
      label: 'Vendor Emergency',
      actions: ['chat', 'details'],
    },
    emergency: {
      color: 'bg-error/10 text-error',
      icon: AlertCircle,
      label: 'Emergency - Replacement in Progress',
      actions: ['chat', 'details'],
    },
  };

  const config = statusConfig[bookingData.status] || statusConfig.pending;
  const StatusIcon = config.icon;

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(date);
  };

  // Days until event
  const getDayText = () => {
    if (bookingData.daysUntil < 0) return 'Event completed';
    if (bookingData.daysUntil === 0) return 'Today!';
    if (bookingData.daysUntil === 1) return 'Tomorrow';
    return `${bookingData.daysUntil} days away`;
  };

  // Payment status badge
  const paymentBadge = {
    paid: { color: 'bg-success/10 text-success', label: 'Paid' },
    pending: { color: 'bg-warning/10 text-warning', label: 'Payment Pending' },
    refunded: { color: 'bg-info/10 text-info', label: 'Refunded' },
  };

  const paymentBadgeConfig = paymentBadge[bookingData.paymentStatus] || paymentBadge.pending;

  return (
    <Card
      className={cn(
        'overflow-hidden hover:shadow-lg transition-all duration-300',
        className
      )}
    >
      {/* Header with vendor info and status */}
      <CardHeader className="pb-3 border-b border-border">
        <div className="flex items-start justify-between gap-3">
          {/* Vendor Info */}
          <div className="flex gap-3 flex-1 min-w-0">
            <img
              src={bookingData.vendorImage}
              alt={bookingData.vendorName}
              className="w-12 h-12 rounded-lg flex-shrink-0 object-cover"
            />
            <div className="min-w-0 flex-1">
              <h3 className="text-body-md font-semibold text-foreground line-clamp-1">
                {bookingData.vendorName}
              </h3>
              <p className="text-body-sm text-muted-foreground">
                {bookingData.serviceName}
              </p>
              <p className="text-tiny text-muted-foreground">
                ID: {bookingData.bookingId}
              </p>
            </div>
          </div>

          {/* Status Badge */}
          <Badge className={cn('flex gap-1 flex-shrink-0', config.color)}>
            <StatusIcon size={14} />
            <span className="text-tiny">{config.label}</span>
          </Badge>
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent className="p-lg space-y-lg">
        {/* Event Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md bg-muted rounded-lg p-md">
          {/* Date */}
          <div className="flex gap-2 items-start">
            <Calendar size={16} className="text-primary mt-0.5 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-tiny font-semibold text-muted-foreground">EVENT DATE</p>
              <p className="text-body-md font-semibold text-foreground">
                {formatDate(bookingData.eventDate)}
              </p>
              <p className="text-tiny text-muted-foreground">
                {getDayText()}
              </p>
            </div>
          </div>

          {/* Time */}
          <div className="flex gap-2 items-start">
            <Clock size={16} className="text-primary mt-0.5 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-tiny font-semibold text-muted-foreground">TIME</p>
              <p className="text-body-md font-semibold text-foreground line-clamp-2">
                {bookingData.eventTime}
              </p>
            </div>
          </div>

          {/* Location */}
          <div className="flex gap-2 items-start sm:col-span-2">
            <MapPin size={16} className="text-primary mt-0.5 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-tiny font-semibold text-muted-foreground">LOCATION</p>
              <p className="text-body-md font-semibold text-foreground line-clamp-2">
                {bookingData.eventLocation}
              </p>
            </div>
          </div>
        </div>

        {/* Price & Payment Status */}
        <div className="flex items-center justify-between bg-primary/5 rounded-lg p-md border border-primary/10">
          <div>
            <p className="text-tiny font-semibold text-muted-foreground">TOTAL AMOUNT</p>
            <p className="text-h6 font-bold text-primary">
              {bookingData.currency}
              {bookingData.amount.toLocaleString('en-IN')}
            </p>
          </div>
          <Badge className={paymentBadgeConfig.color}>
            {paymentBadgeConfig.label}
          </Badge>
        </div>

        {/* Emergency Banner (if applicable) */}
        {(bookingData.status === 'emergency' || bookingData.status === 'vendor_cancelled_emergency') && (
          <div className="bg-error/5 border border-error/20 rounded-lg p-md space-y-2">
            <p className="text-body-sm font-semibold text-error flex gap-2 items-center">
              <AlertCircle size={16} />
              Replacement in Progress
            </p>
            <p className="text-body-sm text-foreground">
              The original vendor had an emergency. Your booking is protected and we are sourcing the best replacement.
            </p>
            {bookingData.replacementSuggestions.length > 0 && (
              <div className="bg-white/70 border border-error/10 rounded-lg p-2 text-tiny text-foreground">
                {bookingData.replacementSuggestions.length} backup vendors are already shortlisted.
              </div>
            )}
            <Button variant="outline" size="sm" className="w-full">
              View Replacement Details
            </Button>
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-md border-t border-border space-y-2">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => onChat?.()}
              className="gap-1 flex-1 min-w-fit"
            >
              <MessageSquare size={16} />
              Chat
            </Button>

            {bookingData.status === 'confirmed' && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onReschedule?.()}
                  className="flex-1 min-w-fit"
                >
                  Reschedule
                </Button>
                <Button
                  variant="text"
                  size="sm"
                  onClick={() => onCancel?.()}
                  className="text-error flex-1 min-w-fit"
                >
                  Cancel
                </Button>
              </>
            )}

            {bookingData.status === 'pending' && bookingData.paymentStatus === 'pending' && (
              <Button
                variant="premium"
                size="sm"
                onClick={() => onPay?.()}
                className="flex-1 min-w-fit"
              >
                Complete Payment
              </Button>
            )}

            {bookingData.status === 'completed' && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onRate?.()}
                className="flex-1 min-w-fit"
              >
                Rate & Review
              </Button>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => setShowActions(!showActions)}
          >
            {showActions ? 'Hide' : 'Show'} More Options
          </Button>
        </div>

        {/* Expanded Actions */}
        {showActions && (
          <div className="pt-md border-t border-border grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm">Download Invoice</Button>
            <Button variant="outline" size="sm">Track Status</Button>
            <Button variant="outline" size="sm">View Details</Button>
            <Button variant="outline" size="sm">Report Issue</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * BookingsList Component
 * Container for multiple bookings with status filters
 */
export const BookingsList = ({
  bookings = [],
  onChat,
  onReschedule,
  onCancel,
  onRate,
  className,
}) => {
  const [filterStatus, setFilterStatus] = useState('all');

  const filteredBookings = filterStatus === 'all'
    ? bookings
    : bookings.filter((b) => b.status === filterStatus);

  const statusOptions = [
    { value: 'all', label: 'All Bookings', count: bookings.length },
    { value: 'pending', label: 'Pending', count: bookings.filter((b) => b.status === 'pending').length },
    { value: 'confirmed', label: 'Confirmed', count: bookings.filter((b) => b.status === 'confirmed').length },
    { value: 'completed', label: 'Completed', count: bookings.filter((b) => b.status === 'completed').length },
    { value: 'cancelled', label: 'Cancelled', count: bookings.filter((b) => b.status === 'cancelled').length },
  ];

  return (
    <div className={cn('space-y-lg', className)}>
      {/* Filters */}
      <div className="space-y-md">
        <h2 className="text-h4 font-heading">Bookings</h2>
        
        <div className="flex flex-wrap gap-2">
          {statusOptions.map((option) => (
            <Button
              key={option.value}
              variant={filterStatus === option.value ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setFilterStatus(option.value)}
              className="gap-1"
            >
              {option.label}
              <span className="text-tiny ml-1">({option.count})</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Bookings */}
      <div className="space-y-lg">
        {filteredBookings.length > 0 ? (
          filteredBookings.map((booking) => (
            <BookingCard
              key={booking.id}
              booking={booking}
              onChat={onChat}
              onReschedule={onReschedule}
              onCancel={onCancel}
              onRate={onRate}
            />
          ))
        ) : (
          <div className="text-center py-12 bg-muted rounded-lg">
            <p className="text-muted-foreground text-body-md mb-md">
              {filterStatus === 'all'
                ? 'No bookings yet. Start planning your event!'
                : `No ${filterStatus} bookings.`}
            </p>
            <Button variant="primary">Book a Vendor</Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default BookingCard;
