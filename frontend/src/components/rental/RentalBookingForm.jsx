import React, { useState } from 'react';

export default function RentalBookingForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    rental_start: '',
    rental_end: '',
    inventory_item_id: '',
    qty: 1,
    rental_amount: 2000,
    deposit_amount: 1000,
    notes: '',
  });

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          ...form,
          qty: Number(form.qty),
          rental_amount: Number(form.rental_amount),
          deposit_amount: Number(form.deposit_amount),
          rental_start: new Date(form.rental_start).toISOString(),
          rental_end: new Date(form.rental_end).toISOString(),
        });
      }}
    >
      <input className="w-full border rounded p-2" type="datetime-local" required value={form.rental_start} onChange={(e) => update('rental_start', e.target.value)} />
      <input className="w-full border rounded p-2" type="datetime-local" required value={form.rental_end} onChange={(e) => update('rental_end', e.target.value)} />
      <input className="w-full border rounded p-2" placeholder="Inventory Item ID" required value={form.inventory_item_id} onChange={(e) => update('inventory_item_id', e.target.value)} />
      <input className="w-full border rounded p-2" type="number" min="1" placeholder="Quantity" value={form.qty} onChange={(e) => update('qty', e.target.value)} />
      <input className="w-full border rounded p-2" type="number" min="1" placeholder="Rental amount" value={form.rental_amount} onChange={(e) => update('rental_amount', e.target.value)} />
      <input className="w-full border rounded p-2" type="number" min="0" placeholder="Deposit" value={form.deposit_amount} onChange={(e) => update('deposit_amount', e.target.value)} />
      <textarea className="w-full border rounded p-2" placeholder="Notes (optional)" value={form.notes} onChange={(e) => update('notes', e.target.value)} />
      <button className="w-full bg-black text-white rounded p-2" type="submit" disabled={loading}>{loading ? 'Processing...' : 'Continue to payment'}</button>
    </form>
  );
}
