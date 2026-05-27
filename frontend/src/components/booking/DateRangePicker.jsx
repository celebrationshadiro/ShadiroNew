import React, { useMemo } from 'react';

function toDateOnly(value) {
  return String(value || '').split('T')[0];
}

function dateDiffDays(start, end) {
  if (!start || !end) return 0;
  const s = new Date(toDateOnly(start)).getTime();
  const e = new Date(toDateOnly(end)).getTime();
  if (Number.isNaN(s) || Number.isNaN(e) || e <= s) return 0;
  return Math.ceil((e - s) / (1000 * 60 * 60 * 24));
}

function isBlockedDate(dateValue, blockedDates) {
  const d = toDateOnly(dateValue);
  return Array.isArray(blockedDates) && blockedDates.map(toDateOnly).includes(d);
}

export default function DateRangePicker({
  checkIn,
  checkOut,
  onChange,
  blockedDates = [],
  dailyPricePaise = 0,
}) {
  const durationDays = useMemo(() => dateDiffDays(checkIn, checkOut), [checkIn, checkOut]);
  const autoTotalPaise = useMemo(
    () => Math.max(0, Number(durationDays || 0) * Number(dailyPricePaise || 0)),
    [durationDays, dailyPricePaise],
  );

  const checkInBlocked = isBlockedDate(checkIn, blockedDates);
  const checkOutBlocked = isBlockedDate(checkOut, blockedDates);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-sm font-medium">Check-in Date</label>
          <input
            type="date"
            className={`w-full border rounded p-2 ${checkInBlocked ? 'border-red-300 bg-red-50' : ''}`}
            value={checkIn || ''}
            onChange={(e) => onChange?.({ checkIn: e.target.value, checkOut })}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Check-out Date</label>
          <input
            type="date"
            className={`w-full border rounded p-2 ${checkOutBlocked ? 'border-red-300 bg-red-50' : ''}`}
            value={checkOut || ''}
            onChange={(e) => onChange?.({ checkIn, checkOut: e.target.value })}
            required
          />
        </div>
      </div>

      {Array.isArray(blockedDates) && blockedDates.length > 0 ? (
        <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2">
          Blocked dates: {blockedDates.map(toDateOnly).join(', ')}
        </div>
      ) : null}

      <div className="text-sm text-stone-700 rounded border bg-stone-50 p-2">
        <p>Duration: <span className="font-semibold">{durationDays} day(s)</span></p>
        <p>Auto price: <span className="font-semibold">Rs. {Math.floor(autoTotalPaise / 100)}</span></p>
      </div>
    </div>
  );
}

