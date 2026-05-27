"use client";

import React, { useRef, useState } from "react";
import Image from "next/image";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Star, ShieldCheck, MapPin, Truck, ChevronRight } from "lucide-react";

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

interface VendorCardProps {
  vendor: Vendor;
  onSelect: (vendorId: string) => void;
}

export default function VendorCard({ vendor, onSelect }: VendorCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState(false);

  // Framer Motion 3D Tilt Setup
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseXSpring = useSpring(x);
  const mouseYSpring = useSpring(y);

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["10deg", "-10deg"]);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-10deg", "10deg"]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    // Calculate relative mouse position from -0.5 to 0.5
    const relativeX = (e.clientX - rect.left) / width - 0.5;
    const relativeY = (e.clientY - rect.top) / height - 0.5;

    x.set(relativeX);
    y.set(relativeY);
  };

  const handleMouseLeave = () => {
    setHovered(false);
    x.set(0);
    y.set(0);
  };

  const formatPrice = (paise?: number) => {
    if (paise === undefined) return "₹0";
    return `₹${(paise / 100).toLocaleString()}`;
  };

  const minOrder = formatPrice(vendor.min_order_paise ?? 50000); // Defaults to ₹500
  const deliveryFee = formatPrice(vendor.delivery_fee_paise ?? 4900); // Defaults to ₹49

  return (
    <div 
      className="perspective-1000"
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={handleMouseLeave}
    >
      <motion.div
        ref={cardRef}
        style={{
          rotateX: hovered ? rotateX : 0,
          rotateY: hovered ? rotateY : 0,
          transformStyle: "preserve-3d",
        }}
        onClick={() => onSelect(vendor.id)}
        className="cursor-pointer group relative bg-white border border-stone-200 hover:border-transparent rounded-2xl overflow-hidden p-0.5 shadow-md hover:shadow-2xl transition-all duration-300 flex flex-col h-full"
        aria-label={`View grocery shop ${vendor.business_name}`}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelect(vendor.id);
          }
        }}
      >
        {/* Elegant Royal Shimmer Card Border (Visible on Hover) */}
        <div 
          className="absolute inset-0 bg-gradient-to-tr from-brand-gold via-brand-emerald to-brand-blue rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10 pointer-events-none"
        />

        {/* Card Body Container */}
        <div className="bg-white rounded-[14px] overflow-hidden flex flex-col h-full p-4 z-10 flex-grow">
          {/* Header Visual Banner */}
          <div className="relative h-44 w-full rounded-xl overflow-hidden bg-stone-100 mb-4">
            <Image
              src="https://res.cloudinary.com/eventapp/categories/grocery.jpg"
              alt={vendor.business_name}
              fill
              sizes="(max-w-768px) 100vw, 33vw"
              className="object-cover group-hover:scale-105 transition-transform duration-500"
              priority={true}
            />

            {/* Quality & Safety Badges */}
            <div className="absolute top-3 left-3 flex flex-col gap-1.5 z-10">
              <span className="bg-brand-emerald/90 backdrop-blur-sm text-white font-bold text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-md shadow-md flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> Certified Safe
              </span>
            </div>

            {/* Gold Verified Emblem */}
            <span className="absolute top-3 right-3 bg-stone-900/80 backdrop-blur-sm text-brand-gold text-xs font-bold px-2 py-1 rounded-md border border-brand-gold/30">
              👑 Elite
            </span>

            {/* Instant Delivery Badge */}
            <div className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-md text-white font-bold text-xs px-2.5 py-1 rounded-md flex items-center space-x-1.5 shadow-md">
              <Truck className="h-3.5 w-3.5 text-brand-gold" />
              <span>⚡ 40 Mins</span>
            </div>
          </div>

          {/* Details Content Block */}
          <div className="flex-grow flex flex-col justify-between">
            <div>
              {/* City Location & Top Tag */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center text-stone-500 text-xs font-medium space-x-1">
                  <MapPin className="h-3 w-3 text-stone-400" />
                  <span>{vendor.city || "Mumbai"}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Star className="text-brand-gold fill-brand-gold h-3.5 w-3.5" />
                  <span className="text-xs font-bold text-stone-800">{vendor.rating ?? 4.8}</span>
                  <span className="text-[10px] text-stone-400">({vendor.total_reviews ?? 42})</span>
                </div>
              </div>

              {/* Title heading */}
              <h3 className="font-heading text-lg font-bold text-stone-900 mb-2 leading-tight group-hover:text-brand-emerald transition-colors duration-200">
                {vendor.business_name}
              </h3>

              {/* Sub-tags */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {(vendor.tags ?? ["Organic Produce", "Festive Hampers", "Dairy Nobles"]).map((tag) => (
                  <span 
                    key={tag}
                    className="bg-stone-50 text-stone-600 border border-stone-200 text-[10px] font-semibold px-2 py-0.5 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Checkout Pricing Footer */}
            <div className="pt-3.5 border-t border-stone-100 flex items-center justify-between mt-auto">
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] text-stone-400 uppercase font-bold tracking-wide">Min. Order</span>
                <span className="text-sm font-bold text-stone-800">{minOrder}</span>
              </div>

              <div className="flex flex-col gap-0.5 items-end">
                <span className="text-[10px] text-stone-400 uppercase font-bold tracking-wide">Delivery</span>
                <span className="text-xs font-semibold text-brand-emerald-dark">{deliveryFee === "₹0" ? "Free" : deliveryFee}</span>
              </div>

              {/* Enter Shop tap target */}
              <button
                className="bg-stone-900 group-hover:bg-brand-emerald text-white rounded-lg p-2.5 transition-colors duration-300 flex items-center justify-center hover:scale-105 active:scale-95 shadow-md"
                aria-label={`Enter ${vendor.business_name} store`}
                style={{ width: "44px", height: "44px" }}
              >
                <ChevronRight className="h-5 w-5 text-white" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

/* -------------------------------------------------------------
   VendorCardSkeleton: Clean Glassmorphic Pulsating Shimmer Loader
   ------------------------------------------------------------- */
export function VendorCardSkeleton() {
  return (
    <div className="border border-stone-200 bg-white rounded-2xl p-4.5 space-y-4 animate-pulse shadow-sm">
      {/* Visual Header block */}
      <div className="bg-stone-100 rounded-xl h-44 w-full relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-stone-200/50 to-transparent -translate-x-full animate-shimmer" />
      </div>

      {/* Primary details */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="bg-stone-200 h-3 w-1/4 rounded" />
          <div className="bg-stone-200 h-3 w-1/6 rounded" />
        </div>

        <div className="bg-stone-200 h-5 w-3/4 rounded-md" />

        <div className="flex gap-2 pt-1">
          <div className="bg-stone-100 h-5 w-20 rounded-full border border-stone-200" />
          <div className="bg-stone-100 h-5 w-24 rounded-full border border-stone-200" />
        </div>
      </div>

      {/* Base details */}
      <div className="pt-4 border-t border-stone-100 flex items-center justify-between">
        <div className="space-y-1">
          <div className="bg-stone-200 h-2.5 w-12 rounded" />
          <div className="bg-stone-200 h-4.5 w-16 rounded" />
        </div>
        <div className="space-y-1">
          <div className="bg-stone-200 h-2.5 w-12 rounded" />
          <div className="bg-stone-200 h-4.5 w-16 rounded" />
        </div>
        <div className="bg-stone-200 h-10 w-10 rounded-lg" />
      </div>
    </div>
  );
}
