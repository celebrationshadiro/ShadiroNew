"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CreditCard, Truck, CheckCircle, ShieldCheck, Loader2, Sparkles, MapPin } from "lucide-react";
import confetti from "canvas-confetti";

interface CheckoutStepperProps {
  totalPaise: number;
  savingsPaise?: number;
  onSuccess: (orderId: string) => void;
}

export default function CheckoutStepper({ totalPaise, savingsPaise = 0, onSuccess }: CheckoutStepperProps) {
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [address, setAddress] = useState({
    fullName: "",
    phone: "",
    streetAddress: "",
    city: "Mumbai",
    pincode: "",
  });

  const formatPrice = (paise: number) => {
    return `₹${(paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  };

  const handleNextStep = () => {
    if (step === 1) {
      if (!address.fullName || !address.phone || !address.streetAddress || !address.pincode) {
        alert("Please complete all shipping address fields accurately.");
        return;
      }
      setStep(2);
    }
  };

  const handleRazorpaySimulation = () => {
    setIsProcessing(true);

    // Simulate high-fidelity Razorpay payment gate loading
    setTimeout(() => {
      setIsProcessing(false);
      setStep(3);

      // Trigger standard gold success confetti
      const duration = 3 * 1000;
      const end = Date.now() + duration;

      const frame = () => {
        confetti({
          particleCount: 5,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: ["#D4AF37", "#097969"],
        });
        confetti({
          particleCount: 5,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: ["#D4AF37", "#097969"],
        });

        if (Date.now() < end) {
          requestAnimationFrame(frame);
        }
      };
      frame();

      // Trigger standard order completion callback
      const simulatedOrderId = "ord_" + Math.random().toString(36).substring(2, 11);
      onSuccess(simulatedOrderId);
    }, 2500);
  };

  return (
    <div 
      className="bg-white border border-stone-200 rounded-3xl p-6 md:p-10 shadow-2xl max-w-2xl mx-auto"
      role="region"
      aria-label="Checkout Pipeline Stepper"
    >
      {/* 3-Step Guided Header Visual */}
      <div className="flex items-center justify-between mb-10 border-b border-stone-100 pb-6">
        {[
          { label: "Shipping", icon: <Truck className="h-4 w-4" /> },
          { label: "Payment Gateway", icon: <CreditCard className="h-4 w-4" /> },
          { label: "Order Placed", icon: <CheckCircle className="h-4 w-4" /> },
        ].map((item, index) => {
          const stepNum = index + 1;
          const isActive = step === stepNum;
          const isDone = step > stepNum;

          return (
            <div key={item.label} className="flex items-center space-x-2">
              <div
                className={`h-9 w-9 rounded-full flex items-center justify-center border-2 text-xs font-bold transition-all duration-300 ${
                  isDone
                    ? "bg-brand-emerald border-brand-emerald text-white"
                    : isActive
                    ? "bg-white border-brand-gold text-brand-gold shadow-md shadow-brand-gold/20"
                    : "bg-white border-stone-200 text-stone-400"
                }`}
                aria-hidden="true"
              >
                {item.icon}
              </div>
              <span
                className={`text-xs font-bold hidden sm:inline ${
                  isActive ? "text-brand-gold-dark" : isDone ? "text-stone-700" : "text-stone-400"
                }`}
              >
                {item.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Steps Pipeline Content Area */}
      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 15 }}
            className="space-y-6"
          >
            <h3 className="font-heading text-xl font-bold text-stone-900 flex items-center gap-2">
              <MapPin className="h-5 w-5 text-brand-gold" /> Shipping & Delivery Details
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5 col-span-2 md:col-span-1">
                <label className="text-xs font-bold text-stone-500 uppercase tracking-wide">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Aditi Sharma"
                  value={address.fullName}
                  onChange={(e) => setAddress({ ...address, fullName: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-gold transition"
                  style={{ minHeight: "44px" }}
                />
              </div>

              <div className="space-y-1.5 col-span-2 md:col-span-1">
                <label className="text-xs font-bold text-stone-500 uppercase tracking-wide">Contact Number *</label>
                <input
                  type="tel"
                  required
                  placeholder="e.g. +91 99999 99999"
                  value={address.phone}
                  onChange={(e) => setAddress({ ...address, phone: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-gold transition"
                  style={{ minHeight: "44px" }}
                />
              </div>

              <div className="space-y-1.5 col-span-2">
                <label className="text-xs font-bold text-stone-500 uppercase tracking-wide">Street Address *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Apartment, Suite, Villa No, Area"
                  value={address.streetAddress}
                  onChange={(e) => setAddress({ ...address, streetAddress: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-gold transition"
                  style={{ minHeight: "44px" }}
                />
              </div>

              <div className="space-y-1.5 col-span-2 md:col-span-1">
                <label className="text-xs font-bold text-stone-500 uppercase tracking-wide">City</label>
                <input
                  type="text"
                  disabled
                  value={address.city}
                  className="w-full bg-stone-100 border border-stone-200 text-stone-500 rounded-xl p-3 text-sm"
                  style={{ minHeight: "44px" }}
                />
              </div>

              <div className="space-y-1.5 col-span-2 md:col-span-1">
                <label className="text-xs font-bold text-stone-500 uppercase tracking-wide">Pincode *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 400001"
                  value={address.pincode}
                  onChange={(e) => setAddress({ ...address, pincode: e.target.value })}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-gold transition"
                  style={{ minHeight: "44px" }}
                />
              </div>
            </div>

            <button
              onClick={handleNextStep}
              className="w-full bg-stone-900 hover:bg-stone-800 text-white font-bold h-12 rounded-xl transition active:scale-95 shadow-md mt-4"
              style={{ minHeight: "44px" }}
            >
              Continue to Payment
            </button>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 15 }}
            className="space-y-6"
          >
            <h3 className="font-heading text-xl font-bold text-stone-900">
              Select Luxury Payment Mode
            </h3>

            {/* Price review summary */}
            <div className="bg-stone-50 border border-stone-200 rounded-2xl p-4.5 space-y-2.5 text-sm">
              <div className="flex justify-between font-medium text-stone-500">
                <span>Box Subtotal</span>
                <span>{formatPrice(totalPaise)}</span>
              </div>
              {savingsPaise > 0 && (
                <div className="flex justify-between font-medium text-brand-emerald-dark">
                  <span>Royal Savings Discount</span>
                  <span>-{formatPrice(savingsPaise)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-stone-900 border-t border-stone-200 pt-2.5">
                <span>Amount to Pay</span>
                <span className="text-brand-emerald font-heading text-base">{formatPrice(totalPaise)}</span>
              </div>
            </div>

            {/* Razorpay Gateway Simulation box */}
            <div className="bg-gradient-to-tr from-stone-900 to-indigo-950 border border-indigo-900 rounded-2xl p-6 text-white text-center space-y-4 shadow-xl">
              <span className="bg-brand-gold text-stone-900 text-[10px] font-bold uppercase px-3 py-1 rounded-md inline-block">
                Secure API Endpoint Enabled
              </span>
              <h4 className="font-heading text-lg font-bold">
                Razorpay Sovereign Processing Gate
              </h4>
              <p className="text-white/70 text-xs max-w-md mx-auto">
                Securely complete your event groceries booking via cards, netbanking, or UPI. Your transaction is guarded under 100% Shadiro Protection guidelines.
              </p>

              {isProcessing ? (
                <div className="flex flex-col items-center justify-center space-y-2 py-4">
                  <Loader2 className="h-7 w-7 text-brand-gold animate-spin" />
                  <span className="text-xs text-white/70">Connecting secure nodes...</span>
                </div>
              ) : (
                <button
                  onClick={handleRazorpaySimulation}
                  className="bg-gradient-to-r from-brand-gold to-amber-500 hover:from-amber-500 hover:to-brand-gold text-stone-900 font-bold h-12 px-8 rounded-xl transition-all shadow-lg hover:shadow-brand-gold/30 inline-flex items-center justify-center space-x-2 active:scale-95 mx-auto"
                  style={{ minHeight: "44px" }}
                >
                  <ShieldCheck className="h-4.5 w-4.5" />
                  <span>Simulate Pay {formatPrice(totalPaise)}</span>
                </button>
              )}
            </div>

            <button
              onClick={() => setStep(1)}
              disabled={isProcessing}
              className="w-full bg-white border border-stone-200 hover:border-stone-400 text-stone-600 font-bold h-12 rounded-xl transition active:scale-95 disabled:opacity-50"
              style={{ minHeight: "44px" }}
            >
              Back to Address
            </button>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center space-y-6 py-8"
          >
            <div className="h-20 w-20 bg-brand-emerald/10 border-2 border-brand-emerald/30 text-brand-emerald rounded-full flex items-center justify-center mx-auto shadow-inner animate-pulse">
              <CheckCircle className="h-10 w-10 text-brand-emerald" />
            </div>

            <div className="space-y-2">
              <span className="bg-gradient-to-r from-brand-gold to-amber-600 bg-clip-text text-transparent text-xs font-bold uppercase tracking-widest block">
                Transaction Successful
              </span>
              <h3 className="font-heading text-2xl md:text-3xl font-bold text-stone-900">
                Royal Order Confirmed!
              </h3>
              <p className="text-stone-500 text-sm max-w-sm mx-auto">
                Thank you! Your payment of <strong className="text-brand-emerald-dark font-bold">{formatPrice(totalPaise)}</strong> has completed. Our vendors are hand-picking your selections.
              </p>
            </div>

            <div className="bg-stone-50 border border-stone-200 rounded-2xl p-4.5 max-w-sm mx-auto text-xs text-stone-600 space-y-1.5 shadow-sm text-left">
              <p className="font-semibold text-stone-850">Delivery Destination:</p>
              <p>{address.fullName}</p>
              <p>{address.streetAddress}</p>
              <p>Pin Code: {address.pincode}</p>
            </div>

            <div className="flex items-center justify-center space-x-1 text-[10px] text-stone-400 font-bold uppercase tracking-wide">
              <Sparkles className="h-3.5 w-3.5 text-brand-gold fill-brand-gold" />
              <span>Sovereign Delivery Commenced</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
