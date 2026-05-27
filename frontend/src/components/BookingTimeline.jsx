import React from 'react';

const timelines = {
  service: ['vendor_pending', 'vendor_accepted', 'confirmed', 'in_progress', 'completed', 'payout_pending', 'payout_released'],
  grocery: ['confirmed', 'in_progress', 'completed', 'payout_released'],
  rental: ['vendor_pending', 'vendor_accepted', 'confirmed', 'in_progress', 'completed', 'payout_released'],
};

export default function BookingTimeline({ categoryType, status }) {
  const steps = timelines[categoryType] || timelines.service;
  const activeIndex = Math.max(steps.indexOf(status), 0);

  return (
    <div className="space-y-2">
      {steps.map((step, index) => (
        <div key={step} className={`p-2 rounded border ${index <= activeIndex ? 'bg-green-50 border-green-300' : 'bg-white border-stone-200'}`}>
          <span className="text-sm font-medium">{step.replace(/_/g, ' ').toUpperCase()}</span>
        </div>
      ))}
    </div>
  );
}
