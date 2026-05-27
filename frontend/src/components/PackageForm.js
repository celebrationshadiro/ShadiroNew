import React, { useMemo, useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const TIER_OPTIONS = [
  { value: 'basic', label: 'Basic' },
  { value: 'standard', label: 'Standard' },
  { value: 'premium', label: 'Premium' },
  { value: 'custom', label: 'Custom' },
];

const toList = (value) =>
  value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

export const PackageForm = ({ initialData, items, onSubmit, submitting }) => {
  const [form, setForm] = useState({
    name: initialData?.name || '',
    tier: initialData?.tier || 'basic',
    description: initialData?.description || '',
    price: initialData?.price || '',
    min_guests: initialData?.min_guests || '',
    max_guests: initialData?.max_guests || '',
    services_included: (initialData?.services_included || []).join('\n'),
    is_customizable: initialData?.is_customizable || false,
  });

  const [selectedItems, setSelectedItems] = useState(() => {
    const existing = initialData?.package_items || [];
    return existing.map((i) => ({
      id: i.item_id || i.id,
      qty: i.qty || 1,
    }));
  });

  const itemsMap = useMemo(() => {
    const map = {};
    (items || []).forEach((item) => {
      map[item.id] = item;
    });
    return map;
  }, [items]);

  const toggleItem = (id) => {
    setSelectedItems((prev) => {
      const exists = prev.find((p) => p.id === id);
      if (exists) return prev.filter((p) => p.id !== id);
      return [...prev, { id, qty: 1 }];
    });
  };

  const updateQty = (id, qty) => {
    setSelectedItems((prev) =>
      prev.map((p) => (p.id === id ? { ...p, qty: Math.max(1, qty) } : p))
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const packageItems = selectedItems
      .map((sel) => {
        const item = itemsMap[sel.id];
        if (!item) return null;
        return {
          item_id: item.id,
          name: item.name,
          qty: sel.qty,
          unit_price: item.unit_price,
          unit: item.unit,
          total_price: item.unit_price * sel.qty,
        };
      })
      .filter(Boolean);

    onSubmit?.({
      ...form,
      price: form.price ? parseFloat(form.price) : 0,
      min_guests: form.min_guests ? parseInt(form.min_guests, 10) : null,
      max_guests: form.max_guests ? parseInt(form.max_guests, 10) : null,
      services_included: toList(form.services_included),
      package_items: packageItems,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card className="p-6 bg-white rounded-2xl border border-stone-100 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>Package Name *</Label>
            <Input
              className="mt-2"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Wedding Essentials"
              required
            />
          </div>
          <div>
            <Label>Tier *</Label>
            <Select
              value={form.tier}
              onValueChange={(value) => setForm({ ...form, tier: value, is_customizable: value === 'custom' })}
            >
              <SelectTrigger className="mt-2 h-10 rounded-lg">
                <SelectValue placeholder="Select tier" />
              </SelectTrigger>
              <SelectContent>
                {TIER_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label>Description</Label>
          <Textarea
            className="mt-2"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Short description of what's included"
            rows={3}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label>Price (₹)</Label>
            <Input
              type="number"
              min={0}
              className="mt-2"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
              placeholder="25000"
              disabled={form.tier === 'custom'}
            />
            {form.tier === 'custom' && (
              <p className="text-xs text-stone-500 mt-1">Custom pricing is calculated at booking.</p>
            )}
          </div>
          <div>
            <Label>Min Guests</Label>
            <Input
              type="number"
              min={0}
              className="mt-2"
              value={form.min_guests}
              onChange={(e) => setForm({ ...form, min_guests: e.target.value })}
              placeholder="50"
            />
          </div>
          <div>
            <Label>Max Guests</Label>
            <Input
              type="number"
              min={0}
              className="mt-2"
              value={form.max_guests}
              onChange={(e) => setForm({ ...form, max_guests: e.target.value })}
              placeholder="300"
            />
          </div>
        </div>

        <div>
          <Label>Services Included (one per line)</Label>
          <Textarea
            className="mt-2"
            value={form.services_included}
            onChange={(e) => setForm({ ...form, services_included: e.target.value })}
            placeholder="Sound system\nLights\n4-hour performance"
            rows={4}
          />
        </div>
      </Card>

      <Card className="p-6 bg-white rounded-2xl border border-stone-100">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">Package Items</h3>
            <p className="text-sm text-stone-500">Select items and quantities for fixed packages.</p>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="p-4 bg-stone-50 rounded-lg text-stone-600">
            No service items found. Add items in your vendor profile to build packages.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {items.map((item) => {
              const selected = selectedItems.find((s) => s.id === item.id);
              return (
                <div key={item.id} className="border rounded-lg p-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-xs text-stone-500">₹{item.unit_price}/{item.unit}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={!!selected}
                      onChange={() => toggleItem(item.id)}
                    />
                    {selected && (
                      <Input
                        type="number"
                        min={1}
                        value={selected.qty}
                        onChange={(e) => updateQty(item.id, parseInt(e.target.value || '1', 10))}
                        className="w-20 h-9"
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <Button
        type="submit"
        className="w-full bg-primary hover:bg-primary/90 h-12 rounded-full"
        disabled={submitting}
      >
        {submitting ? 'Saving...' : 'Save Package'}
      </Button>
    </form>
  );
};

export default PackageForm;
