import React, { useEffect, useMemo, useState } from 'react';
import apiClient from '../../lib/apiClient';

function fmtDate(dateStr, timeStr) {
  if (!dateStr) return '-';
  const date = new Date(`${dateStr}T${timeStr || '00:00'}:00`);
  if (Number.isNaN(date.getTime())) return `${dateStr} ${timeStr || ''}`.trim();
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function secondsLeft(deadline) {
  if (!deadline) return 0;
  const ms = new Date(deadline).getTime() - Date.now();
  return Math.max(0, Math.floor(ms / 1000));
}

function formatCountdown(totalSeconds) {
  const s = Math.max(0, Number(totalSeconds || 0));
  const hh = String(Math.floor(s / 3600)).padStart(2, '0');
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

function normalizeStatus(status) {
  return String(status || '')
    .trim()
    .toUpperCase()
    .replace(/\s+/g, '_');
}

export default function VendorBookingCard({
  booking,
  onActionDone,
  className = '',
}) {
  const [actionLoading, setActionLoading] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [leftSeconds, setLeftSeconds] = useState(secondsLeft(booking?.vendor_response_deadline));

  const status = normalizeStatus(booking?.status);
  const isPendingVendor = status === 'PENDING_VENDOR';
  const isExpired = leftSeconds <= 0;

  useEffect(() => {
    setLeftSeconds(secondsLeft(booking?.vendor_response_deadline));
    if (!booking?.vendor_response_deadline) return undefined;
    const id = setInterval(() => {
      setLeftSeconds(secondsLeft(booking?.vendor_response_deadline));
    }, 1000);
    return () => clearInterval(id);
  }, [booking?.vendor_response_deadline]);

  const statusBadge = useMemo(() => {
    if (status === 'PENDING_VENDOR') return 'bg-amber-100 text-amber-700 border-amber-200';
    if (status === 'CONFIRMED') return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    if (status === 'IN_PROGRESS') return 'bg-blue-100 text-blue-700 border-blue-200';
    if (status === 'COMPLETED') return 'bg-indigo-100 text-indigo-700 border-indigo-200';
    if (status === 'CANCELLED' || status === 'REFUNDED') return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-stone-100 text-stone-700 border-stone-200';
  }, [status]);

  const actionApiCall = async (action) => {
    setActionLoading(true);
    setError('');
    try {
      await apiClient.post(`/bookings/service/${booking.id}/vendor-action`, {
        action,
        reason: reason || undefined,
      });
      if (typeof onActionDone === 'function') onActionDone(action, booking);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || `Failed to ${action} booking`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className={`rounded-xl border bg-white p-4 space-y-3 ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-stone-500">Booking ID</p>
          <p className="text-sm font-semibold">{booking?.id || '-'}</p>
          <p className="text-sm text-stone-600 mt-1">
            {booking?.category_slug || 'service'} | Guests: {booking?.guest_count || '-'}
          </p>
        </div>
        <span className={`px-2.5 py-1 text-xs border rounded-full ${statusBadge}`}>
          {status.replace(/_/g, ' ')}
        </span>
      </div>

      <div className="text-sm text-stone-700 space-y-1">
        <p><span className="text-stone-500">Event:</span> {fmtDate(booking?.event_date, booking?.event_time)}</p>
        <p><span className="text-stone-500">Package:</span> {booking?.package_id || '-'}</p>
        <p><span className="text-stone-500">Amount:</span> Rs. {Number(booking?.amount_paise || 0) / 100}</p>
      </div>

      {isPendingVendor ? (
        <div className={`rounded-lg border p-2 text-sm ${isExpired ? 'border-red-300 bg-red-50 text-red-700' : 'border-amber-300 bg-amber-50 text-amber-700'}`}>
          Vendor response deadline: {formatCountdown(leftSeconds)}
        </div>
      ) : null}

      {isPendingVendor ? (
        <div className="space-y-2">
          <input
            type="text"
            className="w-full rounded border p-2 text-sm"
            placeholder="Reason (optional for accept, required for reject)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              className="w-full rounded bg-emerald-600 text-white p-2 text-sm disabled:opacity-60"
              onClick={() => actionApiCall('accept')}
              disabled={actionLoading || isExpired}
            >
              {actionLoading ? 'Working...' : 'Accept'}
            </button>
            <button
              type="button"
              className="w-full rounded bg-red-600 text-white p-2 text-sm disabled:opacity-60"
              onClick={() => actionApiCall('reject')}
              disabled={actionLoading || !reason.trim()}
            >
              {actionLoading ? 'Working...' : 'Reject'}
            </button>
          </div>
        </div>
      ) : null}

      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}

