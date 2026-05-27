import React, { useMemo } from 'react';

function resolveAvailableQty(item) {
  const total = Number(item?.total_qty ?? item?.stock_qty ?? 0);
  const reserved = Number(item?.reserved_qty ?? 0);
  const sold = Number(item?.sold_qty ?? 0);
  const computed = total - reserved - sold;
  if (Number.isFinite(computed)) return Math.max(0, computed);
  return Math.max(0, Number(item?.stock_qty ?? 0));
}

export default function StockBadge({ item }) {
  const available = useMemo(() => resolveAvailableQty(item), [item]);

  if (!item?.is_available || available <= 0) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium bg-stone-200 text-stone-600">
        Out of Stock
      </span>
    );
  }

  if (available <= 2) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium bg-amber-100 text-amber-700">
        Low Stock ({available} left)
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium bg-emerald-100 text-emerald-700">
      In Stock ({available} left)
    </span>
  );
}

