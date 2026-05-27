import React, { useState } from 'react';

export default function ServiceBookingForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    event_date: '',
    start_time: '',
    end_time: '',
    event_city: '',
    event_location: '',
    token_amount: 999,
    notes: '',
  });

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
    >
      <input className="w-full border rounded p-2" type="date" required value={form.event_date} onChange={(e) => update('event_date', e.target.value)} />
      <div className="grid grid-cols-2 gap-2">
        <input className="border rounded p-2" type="time" required value={form.start_time} onChange={(e) => update('start_time', e.target.value)} />
        <input className="border rounded p-2" type="time" required value={form.end_time} onChange={(e) => update('end_time', e.target.value)} />
      </div>
      <input className="w-full border rounded p-2" placeholder="City" required value={form.event_city} onChange={(e) => update('event_city', e.target.value)} />
      <input className="w-full border rounded p-2" placeholder="Venue / location" required value={form.event_location} onChange={(e) => update('event_location', e.target.value)} />
      <input className="w-full border rounded p-2" type="number" min="1" placeholder="Token amount" value={form.token_amount} onChange={(e) => update('token_amount', Number(e.target.value))} />
      <textarea className="w-full border rounded p-2" placeholder="Notes (optional)" value={form.notes} onChange={(e) => update('notes', e.target.value)} />
      <button className="w-full bg-black text-white rounded p-2" type="submit" disabled={loading}>{loading ? 'Processing...' : 'Continue to payment'}</button>
    </form>
  );
}
