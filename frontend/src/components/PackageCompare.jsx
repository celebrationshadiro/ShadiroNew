import React from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';

const normalizePackages = (pkgs = []) =>
  pkgs.map((p) => ({
    id: p.id,
    name: p.name,
    price: p.price || 0,
    duration: p.hours || p.duration_hours || null,
    services: p.services_included || p.services || [],
    items: p.items_included || [],
    description: p.description,
  }));

const PackageCompare = ({ packages = [], onSelect }) => {
  const data = normalizePackages(packages).slice(0, 4); // keep compact
  if (!data.length) return null;
  const minServices = Math.min(...data.map((p) => (p.services || []).length));
  const minPrice = Math.min(...data.map((p) => p.price || 0));

  return (
    <Card className="p-4 md:p-6 bg-white border border-stone-100 rounded-2xl shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-primary/80">Package Compare</p>
          <h3 className="text-lg font-semibold text-stone-900">Pick what fits best</h3>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {data.map((pkg) => (
          <Card key={pkg.id} className="p-4 border border-stone-100 rounded-xl bg-white">
            <p className="text-sm font-semibold text-stone-900 mb-1">{pkg.name}</p>
            <p className="text-lg font-bold text-primary mb-1">₹{pkg.price?.toLocaleString()}</p>
            {pkg.duration && (
              <p className="text-xs text-stone-500 mb-1">{pkg.duration} hrs</p>
            )}
            <p className="text-xs text-stone-500 mb-2">
              {pkg.services.length} services {pkg.items.length ? `• ${pkg.items.length} items` : ''}
            </p>
            {pkg.description && (
              <p className="text-xs text-stone-600 line-clamp-3 mb-2">{pkg.description}</p>
            )}
            {pkg.services.length > 0 && (
              <ul className="text-xs text-stone-600 space-y-1 mb-3">
                {pkg.services.slice(0, 3).map((s, idx) => (
                  <li key={idx}>• {s}</li>
                ))}
              </ul>
            )}
            <p className="text-[11px] text-primary font-medium mb-3">
              {pkg.services.length - minServices > 0
                ? `+${pkg.services.length - minServices} more services than base`
                : 'Core coverage'}
              {pkg.price > minPrice ? ` • +₹${(pkg.price - minPrice).toLocaleString()} upgrade` : ' • Best value'}
            </p>
            <Button
              size="sm"
              className="w-full rounded-full"
              variant="outline"
              onClick={() => onSelect && onSelect(pkg)}
            >
              Select
            </Button>
          </Card>
        ))}
      </div>
    </Card>
  );
};

export default PackageCompare;
