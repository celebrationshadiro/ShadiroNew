'use client';

import React, { useState } from 'react';

export default function CheckoutPage() {
  const [processing, setProcessing] = useState(false);

  const handleCheckout = () => {
    setProcessing(true);
    setTimeout(() => {
      setProcessing(false);
      alert('Mock payment successfully completed!');
    }, 2000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 flex-grow w-full">
      <div className="bg-white border border-stone-200 rounded-2xl p-6 md:p-10 shadow-sm max-w-2xl mx-auto">
        <h1 className="font-serif text-3xl font-bold text-stone-900 mb-6">Payment Checkout</h1>
        <div className="border border-stone-150 rounded-xl p-5 mb-8">
          <div className="flex justify-between font-bold text-stone-850 border-b border-stone-100 pb-3 mb-3">
            <span>Product Subtotal</span>
            <span>₹4,999.00</span>
          </div>
          <div className="flex justify-between text-sm text-stone-500 mb-2">
            <span>Fulfillment Commission</span>
            <span>Included</span>
          </div>
          <div className="flex justify-between text-sm text-stone-500 mb-4">
            <span>Logistics Fees</span>
            <span>₹120.00</span>
          </div>
          <div className="flex justify-between font-serif text-xl font-bold text-pink-600">
            <span>Total Payable</span>
            <span>₹5,119.00</span>
          </div>
        </div>

        <button
          onClick={handleCheckout}
          disabled={processing}
          className="w-full bg-pink-600 hover:bg-pink-700 disabled:bg-stone-300 text-white font-bold py-4 rounded-xl shadow-md transition flex items-center justify-center space-x-2"
          aria-label="Proceed with payment checkout"
        >
          {processing ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Processing Transaction...</span>
            </>
          ) : (
            <span>Pay securely via Razorpay</span>
          )}
        </button>
      </div>
    </div>
  );
}
