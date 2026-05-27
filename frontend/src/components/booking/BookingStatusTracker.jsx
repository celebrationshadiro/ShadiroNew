import React, { useMemo } from 'react';

const FLOW_STEPS = {
  SERVICE: ['Intent', 'Payment', 'Vendor Review', 'Confirmed', 'In Progress', 'Done'],
  RENTAL: ['Intent', 'Deposit', 'Balance Due', 'Confirmed', 'In Progress', 'Done'],
  GROCERY: ['Cart', 'Reserved', 'Payment', 'Confirmed', 'Processing', 'Shipped', 'Done'],
};

function normalize(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '_');
}

function resolveGroup(group, categoryType) {
  const g = normalize(group);
  if (g === 'service') return 'SERVICE';
  if (g === 'rental') return 'RENTAL';
  if (g === 'grocery') return 'GROCERY';

  const c = normalize(categoryType);
  if (c === 'service') return 'SERVICE';
  if (c === 'rental') return 'RENTAL';
  if (c === 'grocery') return 'GROCERY';
  return 'SERVICE';
}

function indexForService(status) {
  const s = normalize(status);
  if (['intent_created', 'pending', 'awaiting_payment'].includes(s)) return 0;
  if (['payment_pending_verification', 'token_paid', 'payment_received'].includes(s)) return 1;
  if (['vendor_pending', 'pending_vendor', 'vendor_accepted', 'vendor_rejected', 'vendor_countered'].includes(s)) return 2;
  if (s === 'confirmed') return 3;
  if (s === 'in_progress') return 4;
  if (['completed', 'payout_pending', 'payout_released'].includes(s)) return 5;
  return 0;
}

function indexForRental(status) {
  const s = normalize(status);
  if (['intent_created', 'pending', 'awaiting_payment'].includes(s)) return 0;
  if (['deposit_paid', 'token_paid', 'payment_received'].includes(s)) return 1;
  if (['balance_due', 'balance_pending'].includes(s)) return 2;
  if (s === 'confirmed') return 3;
  if (s === 'in_progress') return 4;
  if (['completed', 'payout_released'].includes(s)) return 5;
  return 0;
}

function indexForGrocery(status, fulfillmentStatus) {
  const s = normalize(status);
  const f = normalize(fulfillmentStatus);
  if (['cart', 'draft'].includes(s)) return 0;
  if (['reserved', 'lock_active'].includes(s)) return 1;
  if (['awaiting_payment', 'payment_pending_verification', 'token_paid', 'payment_received'].includes(s)) return 2;
  if (['confirmed'].includes(s) && !f) return 3;
  if (f === 'processing') return 4;
  if (f === 'shipped') return 5;
  if (['completed', 'delivered'].includes(s)) return 6;
  if (s === 'confirmed') return 3;
  return 0;
}

function getActiveStepIndex(group, status, fulfillmentStatus) {
  if (group === 'SERVICE') return indexForService(status);
  if (group === 'RENTAL') return indexForRental(status);
  return indexForGrocery(status, fulfillmentStatus);
}

export default function BookingStatusTracker({
  group,
  categoryType,
  status,
  fulfillmentStatus,
}) {
  const resolvedGroup = resolveGroup(group, categoryType);
  const steps = FLOW_STEPS[resolvedGroup] || FLOW_STEPS.SERVICE;
  const activeIndex = useMemo(
    () => getActiveStepIndex(resolvedGroup, status, fulfillmentStatus),
    [resolvedGroup, status, fulfillmentStatus],
  );

  return (
    <div className="space-y-2">
      {steps.map((step, idx) => {
        const done = idx <= activeIndex;
        return (
          <div
            key={`${resolvedGroup}_${step}`}
            className={`rounded-lg border px-3 py-2 text-sm ${
              done ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : 'border-stone-200 bg-white text-stone-500'
            }`}
          >
            {step}
          </div>
        );
      })}
    </div>
  );
}

