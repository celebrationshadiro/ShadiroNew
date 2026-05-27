"use client";

import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ShoppingBag, Trash2, Calendar, Sparkles, AlertCircle, ShoppingCart } from "lucide-react";

interface CartItem {
  id: string;
  name: string;
  price_paise: number;
  quantity: number;
  vendor_id: string;
  vendor_name: string;
  image?: string;
  original_price_paise?: number; // Used for savings badge
}

interface MultiVendorCartProps {
  isOpen: boolean;
  onClose: () => void;
  cartItems: CartItem[];
  onUpdateQuantity: (id: string, newQty: number) => void;
  onRemoveItem: (id: string) => void;
  onCheckout: (slots: Record<string, string>) => void;
}

export default function MultiVendorCart({
  isOpen,
  onClose,
  cartItems,
  onUpdateQuantity,
  onRemoveItem,
  onCheckout,
}: MultiVendorCartProps) {
  // State tracking delivery slot pickers per vendor ID
  const [deliverySlots, setDeliverySlots] = React.useState<Record<string, string>>({});

  // Close drawer on ESC keydown
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Group items by vendor
  const groupedItems = cartItems.reduce((acc, item) => {
    if (!acc[item.vendor_id]) {
      acc[item.vendor_id] = {
        vendorName: item.vendor_name,
        items: [],
      };
    }
    acc[item.vendor_id].items.push(item);
    return acc;
  }, {} as Record<string, { vendorName: string; items: CartItem[] }>);

  // Default missing delivery slots on load
  useEffect(() => {
    const initialSlots = { ...deliverySlots };
    let changed = false;
    Object.keys(groupedItems).forEach((vId) => {
      if (!initialSlots[vId]) {
        initialSlots[vId] = "⚡ Express Delivery (40 mins)";
        changed = true;
      }
    });
    if (changed) {
      setDeliverySlots(initialSlots);
    }
  }, [groupedItems]);

  const handleSlotChange = (vendorId: string, slot: string) => {
    setDeliverySlots((prev) => ({
      ...prev,
      [vendorId]: slot,
    }));
  };

  // Safe integer-based calculations (paise)
  const calculateTotals = () => {
    let subtotal = 0;
    let savings = 0;
    let deliveryFee = 0;

    cartItems.forEach((item) => {
      subtotal += item.price_paise * item.quantity;
      if (item.original_price_paise && item.original_price_paise > item.price_paise) {
        savings += (item.original_price_paise - item.price_paise) * item.quantity;
      }
    });

    // Add ₹49 paise per active vendor as simulated shipping fee
    const vendorCount = Object.keys(groupedItems).length;
    deliveryFee = vendorCount * 4900;

    const total = subtotal + deliveryFee;

    return {
      subtotal: subtotal / 100,
      savings: savings / 100,
      deliveryFee: deliveryFee / 100,
      total: total / 100,
    };
  };

  const totals = calculateTotals();

  const SLOT_OPTIONS = [
    "⚡ Express Delivery (40 mins)",
    "🌅 Morning Express (8:00 AM - 12:00 PM)",
    "🌆 Evening Elegant (4:00 PM - 8:00 PM)",
    "📅 Scheduled: Tomorrow (10:00 AM - 2:00 PM)"
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Elegant dark backdrop overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-stone-950 z-50 transition-opacity"
            aria-hidden="true"
          />

          {/* Sliding Bottom-Sheet / Right Panel (Responsive Layout) */}
          <motion.div
            initial={{ y: "100%", x: 0 }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 220 }}
            className="fixed inset-x-0 bottom-0 md:inset-y-0 md:left-auto md:right-0 md:w-[480px] bg-stone-50 border-t md:border-t-0 md:border-l border-stone-200 z-50 flex flex-col max-h-[92vh] md:max-h-screen rounded-t-3xl md:rounded-t-none md:rounded-l-3xl shadow-2xl"
            role="dialog"
            aria-label="Shopping Cart Drawer"
            tabIndex={-1}
          >
            {/* Mobile Drag Indicator Handle */}
            <div className="w-12 h-1 bg-stone-300 rounded-full mx-auto my-3 md:hidden" />

            {/* Header section */}
            <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-white md:rounded-tl-3xl">
              <div className="flex items-center space-x-2.5">
                <ShoppingBag className="text-brand-emerald h-5 w-5" />
                <h2 className="font-heading text-xl font-bold text-stone-900">Your Celebration Box</h2>
                <span className="bg-stone-100 text-stone-700 text-xs font-bold px-2.5 py-0.5 rounded-full">
                  {cartItems.length}
                </span>
              </div>
              <button
                onClick={onClose}
                className="text-stone-400 hover:text-stone-700 rounded-full p-2.5 transition active:scale-90"
                aria-label="Close Shopping Cart"
                style={{ width: "44px", height: "44px" }}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Scrollable Cart Items Container */}
            <div className="flex-grow overflow-y-auto px-6 py-4 space-y-6">
              {cartItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="bg-stone-100 text-stone-400 p-6 rounded-full mb-4">
                    <ShoppingCart className="h-12 w-12" />
                  </div>
                  <h3 className="text-lg font-bold text-stone-850 mb-1">Your Box is Empty</h3>
                  <p className="text-stone-500 text-sm max-w-xs">
                    Browse our premium local catalog to select fresh greens, truffles, or wedding ingredients!
                  </p>
                </div>
              ) : (
                Object.entries(groupedItems).map(([vendorId, group]) => (
                  <section 
                    key={vendorId}
                    className="bg-white border border-stone-200 rounded-2xl p-4 shadow-sm space-y-4"
                    aria-label={`Items from ${group.vendorName}`}
                  >
                    {/* Group Vendor Header */}
                    <div className="flex items-center justify-between pb-2.5 border-b border-stone-100">
                      <span className="font-heading text-sm font-bold text-stone-900 tracking-wide flex items-center gap-1.5">
                        🏪 {group.vendorName}
                      </span>
                      <span className="bg-stone-50 text-[10px] font-bold text-stone-500 px-2 py-0.5 rounded-md border border-stone-200 uppercase">
                        Vendor Batch
                      </span>
                    </div>

                    {/* Vendor Specific Grocery List */}
                    <div className="space-y-3.5">
                      {group.items.map((item) => (
                        <div 
                          key={item.id}
                          className="flex items-center justify-between space-x-3 text-sm"
                        >
                          <div className="flex items-center space-x-3 flex-1 min-w-0">
                            <div className="h-12 w-12 rounded-lg bg-stone-100 border border-stone-200 overflow-hidden flex-shrink-0 relative">
                              <img
                                src={item.image || "https://res.cloudinary.com/eventapp/categories/grocery.jpg"}
                                alt={item.name}
                                className="object-cover h-full w-full"
                              />
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="font-semibold text-stone-800 truncate">{item.name}</p>
                              <p className="text-xs text-brand-emerald-dark font-medium">
                                ₹{(item.price_paise / 100).toFixed(2)}
                              </p>
                            </div>
                          </div>

                          {/* Interactive Incrementor & Delete controls (touch targets min 44px) */}
                          <div className="flex items-center space-x-2">
                            <div className="flex items-center bg-stone-100 border border-stone-200 rounded-lg overflow-hidden h-9">
                              <button
                                onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                                className="px-2.5 hover:bg-stone-200 transition font-bold text-stone-600"
                                style={{ minHeight: "36px", minWidth: "36px" }}
                                aria-label="Decrease quantity"
                              >
                                -
                              </button>
                              <span className="px-2 font-bold text-stone-800 text-xs min-w-[20px] text-center">
                                {item.quantity}
                              </span>
                              <button
                                onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                                className="px-2.5 hover:bg-stone-200 transition font-bold text-stone-600"
                                style={{ minHeight: "36px", minWidth: "36px" }}
                                aria-label="Increase quantity"
                              >
                                +
                              </button>
                            </div>

                            <button
                              onClick={() => onRemoveItem(item.id)}
                              className="text-stone-400 hover:text-red-500 p-2.5 transition active:scale-90"
                              style={{ width: "44px", height: "44px" }}
                              aria-label={`Remove ${item.name} from cart`}
                            >
                              <Trash2 className="h-4.5 w-4.5" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Isolated Delivery Slot Selector for this specific vendor */}
                    <div className="bg-stone-50 rounded-xl p-3 border border-stone-200 space-y-1.5">
                      <label 
                        className="text-[10px] font-bold text-stone-500 uppercase tracking-wider flex items-center gap-1.5"
                        htmlFor={`delivery-slot-${vendorId}`}
                      >
                        <Calendar className="h-3.5 w-3.5 text-brand-emerald" />
                        Delivery Slot for {group.vendorName}
                      </label>
                      <select
                        id={`delivery-slot-${vendorId}`}
                        value={deliverySlots[vendorId] || ""}
                        onChange={(e) => handleSlotChange(vendorId, e.target.value)}
                        className="w-full bg-white border border-stone-200 rounded-lg p-2 text-xs font-semibold text-stone-700 focus:outline-none focus:ring-2 focus:ring-brand-emerald transition"
                        style={{ minHeight: "40px" }}
                      >
                        {SLOT_OPTIONS.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    </div>
                  </section>
                ))
              )}
            </div>

            {/* Sticky Pricing Calculations & Checkout Trigger */}
            {cartItems.length > 0 && (
              <div className="bg-white border-t border-stone-200 p-6 space-y-4 shadow-2xl z-25">
                {/* Gold Savings Badge Indicator */}
                {totals.savings > 0 && (
                  <div className="bg-gradient-to-r from-amber-50 to-amber-100/50 border border-brand-gold/30 rounded-xl p-3 flex items-center space-x-3.5 shadow-sm animate-pulse">
                    <span className="bg-brand-gold text-stone-900 rounded-full p-1.5 flex items-center justify-center font-bold text-sm">
                      👑
                    </span>
                    <div className="text-xs">
                      <p className="font-bold text-stone-850 flex items-center gap-1">
                        Royal Reward Savings! <Sparkles className="h-3.5 w-3.5 text-brand-gold fill-brand-gold" />
                      </p>
                      <p className="text-stone-500">
                        You are saving <strong className="text-brand-gold-dark font-bold">₹{totals.savings.toFixed(2)}</strong> on this premium cart!
                      </p>
                    </div>
                  </div>
                )}

                {/* Subtotals & Fees */}
                <div className="space-y-2 text-xs font-semibold text-stone-500">
                  <div className="flex justify-between">
                    <span>Items Subtotal</span>
                    <span className="text-stone-850">₹{totals.subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Royal Safe Deliveries ({Object.keys(groupedItems).length} nodes)</span>
                    <span className="text-stone-850">₹{totals.deliveryFee.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-sm text-stone-900 pt-2 border-t border-stone-100">
                    <span>Estimated Total</span>
                    {/* Morphing Number display representation */}
                    <span className="text-brand-emerald font-heading text-lg">
                      ₹{totals.total.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Secure Checkout trigger (tap target min 44px) */}
                <button
                  onClick={() => onCheckout(deliverySlots)}
                  className="w-full bg-gradient-to-r from-brand-emerald to-emerald-700 hover:from-emerald-700 hover:to-brand-emerald text-white font-bold h-12 rounded-xl transition-all shadow-lg hover:shadow-brand-emerald/20 flex items-center justify-center space-x-2 active:scale-95"
                  style={{ minHeight: "44px" }}
                >
                  <Sparkles className="h-4.5 w-4.5 text-brand-gold fill-brand-gold" />
                  <span>Secure Premium Checkout</span>
                </button>

                <div className="flex items-center justify-center space-x-1.5 text-[10px] text-stone-400 font-medium">
                  <AlertCircle className="h-3.5 w-3.5" />
                  <span>All payments strictly parsed in secure integer Paise values.</span>
                </div>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
