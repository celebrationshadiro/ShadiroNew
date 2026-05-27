import React, { useState } from 'react';

export default function GroceryCheckoutForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    item_id: '',
    qty: 1,
    payment_amount: 500,
    delivery_line: '',
    notes: '',
  });

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          items: [{ item_id: form.item_id, qty: Number(form.qty) }],
          payment_amount: Number(form.payment_amount),
          delivery_address: { line1: form.delivery_line },
          notes: form.notes,
        });
      }}
    >
      <input className="w-full border rounded p-2" placeholder="Catalog Item ID" required value={form.item_id} onChange={(e) => update('item_id', e.target.value)} />
      <input className="w-full border rounded p-2" type="number" min="1" placeholder="Quantity" value={form.qty} onChange={(e) => update('qty', e.target.value)} />
      <input className="w-full border rounded p-2" type="number" min="1" placeholder="Payable amount" value={form.payment_amount} onChange={(e) => update('payment_amount', e.target.value)} />
      <input className="w-full border rounded p-2" placeholder="Delivery address" required value={form.delivery_line} onChange={(e) => update('delivery_line', e.target.value)} />
      <textarea className="w-full border rounded p-2" placeholder="Notes (optional)" value={form.notes} onChange={(e) => update('notes', e.target.value)} />
      <button className="w-full bg-black text-white rounded p-2" type="submit" disabled={loading}>{loading ? 'Processing...' : 'Continue to payment'}</button>
    </form>
  );
}
