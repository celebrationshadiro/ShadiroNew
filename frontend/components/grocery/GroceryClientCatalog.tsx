"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShoppingBag, ChevronRight, Sparkles, Store, Plus, ShoppingCart, ArrowLeft } from "lucide-react";
import GroceryHeroSection from "./GroceryHeroSection";
import VendorCard, { VendorCardSkeleton } from "./VendorCard";
import MultiVendorCart from "./MultiVendorCart";
import CheckoutStepper from "../checkout/CheckoutStepper";
import OrderTracking from "./OrderTracking";

interface Vendor {
  id: string;
  business_name: string;
  city?: string;
  rating?: number;
  total_reviews?: number;
  min_order_paise?: number;
  delivery_fee_paise?: number;
  tags?: string[];
}

interface GroceryClientCatalogProps {
  initialVendors: Vendor[];
}

interface CartItem {
  id: string;
  name: string;
  price_paise: number;
  quantity: number;
  vendor_id: string;
  vendor_name: string;
  image?: string;
  original_price_paise?: number;
}

export default function GroceryClientCatalog({ initialVendors }: GroceryClientCatalogProps) {
  const [selectedVendorId, setSelectedVendorId] = useState<string | null>(null);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [checkoutOrderId, setCheckoutOrderId] = useState<string | null>(null);
  const [showCheckout, setShowCheckout] = useState(false);

  // Mock catalog items per vendor category/id
  const SHOP_ITEMS: Record<string, { id: string; name: string; price: number; originalPrice?: number; img: string }[]> = {
    default: [
      { id: "itm-basmati", name: "Heritage Long Grain Basmati (1kg)", price: 24500, originalPrice: 28000, img: "https://res.cloudinary.com/eventapp/categories/grocery.jpg" },
      { id: "itm-ghee", name: "Vedic A2 Cultured Cow Ghee (500ml)", price: 89000, originalPrice: 99500, img: "https://res.cloudinary.com/eventapp/categories/grocery.jpg" },
      { id: "itm-saffron", name: "Royal Kashmiri Kesar / Saffron (1g)", price: 42000, originalPrice: 48000, img: "https://res.cloudinary.com/eventapp/categories/grocery.jpg" },
      { id: "itm-berries", name: "Imperial Gourmet Fresh Blueberry Cup", price: 35000, originalPrice: 35000, img: "https://res.cloudinary.com/eventapp/categories/grocery.jpg" },
      { id: "itm-sourdough", name: "Artisanal Charcoal Sourdough Bread", price: 18000, originalPrice: 21000, img: "https://res.cloudinary.com/eventapp/categories/grocery.jpg" }
    ]
  };

  const selectedVendor = initialVendors.find((v) => v.id === selectedVendorId);
  const storeItems = selectedVendorId ? (SHOP_ITEMS[selectedVendorId] || SHOP_ITEMS.default) : [];

  const handleAddToCart = (item: typeof SHOP_ITEMS.default[0]) => {
    if (!selectedVendor) return;

    setCart((prev) => {
      const existing = prev.find((i) => i.id === item.id);
      if (existing) {
        return prev.map((i) => (i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i));
      }
      return [
        ...prev,
        {
          id: item.id,
          name: item.name,
          price_paise: item.price,
          original_price_paise: item.originalPrice,
          quantity: 1,
          vendor_id: selectedVendor.id,
          vendor_name: selectedVendor.business_name,
          image: item.img,
        },
      ];
    });

    // Pulse animation or toast feedback
    setIsCartOpen(true);
  };

  const handleUpdateQuantity = (itemId: string, newQty: number) => {
    if (newQty <= 0) {
      handleRemoveItem(itemId);
      return;
    }
    setCart((prev) => prev.map((i) => (i.id === itemId ? { ...i, quantity: newQty } : i)));
  };

  const handleRemoveItem = (itemId: string) => {
    setCart((prev) => prev.filter((i) => i.id !== itemId));
  };

  const handleStartCheckout = () => {
    setIsCartOpen(false);
    setShowCheckout(true);
  };

  const handleCheckoutSuccess = (orderId: string) => {
    setCheckoutOrderId(orderId);
    setCart([]); // Clear cart after success
  };

  const getCartTotals = () => {
    let subtotal = 0;
    let savings = 0;
    cart.forEach((i) => {
      subtotal += i.price_paise * i.quantity;
      if (i.original_price_paise) {
        savings += (i.original_price_paise - i.price_paise) * i.quantity;
      }
    });
    return { subtotal, savings };
  };

  const totals = getCartTotals();

  return (
    <div className="space-y-12">
      {/* 1. Hero Title section */}
      <GroceryHeroSection />

      {/* Floating cart trigger button */}
      {cart.length > 0 && !isCartOpen && !showCheckout && (
        <motion.button
          initial={{ scale: 0, y: 50 }}
          animate={{ scale: 1, y: 0 }}
          onClick={() => setIsCartOpen(true)}
          className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-brand-emerald to-emerald-700 hover:from-emerald-700 hover:to-brand-emerald text-white rounded-full p-4.5 shadow-2xl flex items-center space-x-2 border border-brand-emerald/10 scale-105 transition-all duration-300"
          style={{ minHeight: "56px" }}
          aria-label="Open cart box"
        >
          <ShoppingCart className="h-6 w-6 text-brand-gold animate-bounce" />
          <span className="font-bold text-sm">Review Box ({cart.length})</span>
        </motion.button>
      )}

      {/* Primary Routing view controller */}
      <AnimatePresence mode="wait">
        {checkoutOrderId ? (
          /* Active WebSocket Order tracking screen */
          <motion.div
            key="tracking"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="py-12"
          >
            <div className="mb-6 text-center">
              <button
                onClick={() => {
                  setCheckoutOrderId(null);
                  setShowCheckout(false);
                  setSelectedVendorId(null);
                }}
                className="inline-flex items-center space-x-2 bg-stone-100 hover:bg-stone-200 border border-stone-200 hover:border-stone-300 text-stone-700 px-4 py-2.5 rounded-xl font-semibold transition"
                style={{ minHeight: "44px" }}
              >
                <ArrowLeft className="h-4.5 w-4.5" />
                <span>Return to Hyperlocal Marketplace</span>
              </button>
            </div>
            <OrderTracking 
              orderId={checkoutOrderId}
              userId="usr-mumbai-shadiro"
            />
          </motion.div>
        ) : showCheckout ? (
          /* Guided Checkout Stepper */
          <motion.div
            key="checkout"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="py-8"
          >
            <div className="mb-6 text-center">
              <button
                onClick={() => setShowCheckout(false)}
                className="inline-flex items-center space-x-2 bg-stone-100 hover:bg-stone-200 border border-stone-200 text-stone-700 px-4 py-2.5 rounded-xl font-semibold transition"
                style={{ minHeight: "44px" }}
              >
                <ArrowLeft className="h-4.5 w-4.5" />
                <span>Back to Grocery Catalog</span>
              </button>
            </div>

            <CheckoutStepper 
              totalPaise={totals.subtotal}
              savingsPaise={totals.savings}
              onSuccess={handleCheckoutSuccess}
            />
          </motion.div>
        ) : selectedVendorId && selectedVendor ? (
          /* Indvidual Outlets Detail Catalog view */
          <motion.div
            key="vendor-shop"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="bg-white border border-stone-200 rounded-3xl p-6 md:p-8 shadow-sm space-y-8"
          >
            {/* Header store review detail */}
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-stone-100 gap-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setSelectedVendorId(null)}
                  className="bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl p-3.5 transition"
                  style={{ width: "44px", height: "44px" }}
                  aria-label="Back to store listings"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
                <div>
                  <h2 className="font-heading text-2xl md:text-3xl font-bold text-stone-900 flex items-center gap-2">
                    {selectedVendor.business_name}
                  </h2>
                  <p className="text-stone-500 text-sm">
                    📍 {selectedVendor.city || "Mumbai"} • Premium grocery store delivering gourmet yields
                  </p>
                </div>
              </div>

              <div className="bg-stone-50 border border-stone-200 px-4 py-2.5 rounded-xl text-center self-start md:self-auto">
                <span className="text-[10px] font-bold text-stone-400 uppercase tracking-widest block">Rating Shield</span>
                <span className="text-brand-gold font-bold text-sm">★ {selectedVendor.rating || 4.8}</span>
              </div>
            </div>

            {/* Premium Products grid */}
            <div>
              <h3 className="font-heading text-xl font-bold text-stone-900 mb-6 flex items-center gap-2">
                👑 Boutique Festive Pantry
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {storeItems.map((item) => (
                  <article
                    key={item.id}
                    className="bg-stone-50 border border-stone-200 hover:border-brand-gold/30 rounded-2xl p-4 transition-all duration-300 flex flex-col justify-between group shadow-sm hover:shadow-lg"
                  >
                    <div className="relative h-40 w-full rounded-xl overflow-hidden mb-4 bg-stone-100 border border-stone-200">
                      <img
                        src={item.img}
                        alt={item.name}
                        className="object-cover h-full w-full group-hover:scale-103 transition-transform duration-500"
                      />
                      {item.originalPrice && item.originalPrice > item.price && (
                        <span className="absolute top-2 left-2 bg-brand-gold text-stone-900 font-bold text-[9px] uppercase px-2.5 py-0.5 rounded-md shadow-md">
                          Save {Math.round(((item.originalPrice - item.price) / item.originalPrice) * 100)}%
                        </span>
                      )}
                    </div>

                    <div className="space-y-3.5">
                      <div>
                        <h4 className="font-bold text-sm text-stone-850 leading-snug">{item.name}</h4>
                        <p className="text-[10px] text-stone-400 font-bold uppercase tracking-wider mt-1">Festive Pantry</p>
                      </div>

                      <div className="flex items-center justify-between pt-3 border-t border-stone-200/50">
                        <div>
                          {item.originalPrice && item.originalPrice > item.price && (
                            <span className="text-[10px] text-stone-400 line-through block">
                              ₹{(item.originalPrice / 100).toFixed(2)}
                            </span>
                          )}
                          <span className="font-heading text-sm font-bold text-brand-emerald-dark">
                            ₹{(item.price / 100).toFixed(2)}
                          </span>
                        </div>

                        {/* Add to box tap target (min 44px) */}
                        <button
                          onClick={() => handleAddToCart(item)}
                          className="bg-stone-900 hover:bg-brand-emerald text-white rounded-lg px-4.5 h-11 text-xs font-bold transition flex items-center justify-center space-x-1.5 active:scale-95 shadow-md"
                          style={{ minHeight: "44px" }}
                        >
                          <Plus className="h-4 w-4 text-brand-gold" />
                          <span>Add to Box</span>
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </motion.div>
        ) : (
          /* General Hyperlocal Outlets grid */
          <motion.div
            key="listings"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            <h2 className="font-heading text-2xl font-bold text-stone-900 mb-6 flex items-center gap-2">
              <Store className="text-brand-emerald h-6 w-6" /> Premium Outlets in Your Neighborhood
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {initialVendors.map((vendor) => (
                <VendorCard
                  key={vendor.id}
                  vendor={vendor}
                  onSelect={(vId) => setSelectedVendorId(vId)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sliding bottom sheet drawer */}
      <MultiVendorCart
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cartItems={cart}
        onUpdateQuantity={handleUpdateQuantity}
        onRemoveItem={handleRemoveItem}
        onCheckout={handleStartCheckout}
      />
    </div>
  );
}
