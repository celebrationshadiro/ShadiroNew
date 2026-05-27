import React from 'react';
import { Badge } from './ui/badge';

const COLORS = {
  grocery: 'bg-emerald-100 text-emerald-800',
  venue: 'bg-indigo-100 text-indigo-800',
  caterer: 'bg-orange-100 text-orange-800',
  dj: 'bg-purple-100 text-purple-800',
  photographer: 'bg-blue-100 text-blue-800',
  decor: 'bg-rose-100 text-rose-800',
  decorator: 'bg-rose-100 text-rose-800',
  mehandi: 'bg-amber-100 text-amber-800',
  transport: 'bg-sky-100 text-sky-800',
  default: 'bg-stone-100 text-stone-700',
};

const labelMap = {
  grocery: 'Grocery',
  venue: 'Venue',
  caterer: 'Caterer',
  dj: 'DJ',
  photographer: 'Photographer',
  decor: 'Decorator',
  decorator: 'Decorator',
  mehandi: 'Mehandi',
  transport: 'Transport',
};

export function CategoryBadge({ slug = '' }) {
  const key = (slug || '').replace('cat-', '').toLowerCase();
  const color = COLORS[key] || COLORS.default;
  const label = labelMap[key] || (key ? key.charAt(0).toUpperCase() + key.slice(1) : 'Category');
  return <Badge className={color}>{label}</Badge>;
}

export default CategoryBadge;
