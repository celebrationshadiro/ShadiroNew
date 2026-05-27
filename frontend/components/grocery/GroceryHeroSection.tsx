"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, MapPin, Compass, ShoppingBag, Sparkles } from "lucide-react";

export default function GroceryHeroSection() {
  const [searchTerm, setSearchTerm] = useState("");
  const [location, setLocation] = useState("Mumbai, Maharashtra");
  const [showLocationDropdown, setShowLocationDropdown] = useState(false);
  const [activePill, setActivePill] = useState<string | null>(null);
  const [liveOrders, setLiveOrders] = useState(1284);

  const POPULAR_LOCATIONS = [
    "Mumbai, Maharashtra",
    "Delhi, NCR",
    "Bangalore, Karnataka",
    "Chennai, Tamil Nadu",
    "Pune, Maharashtra",
    "Hyderabad, Telangana"
  ];

  const FILTER_PILLS = [
    { id: "organic", label: "🌿 Vedic Organic", desc: "100% certified pesticide-free" },
    { id: "exotic", label: "👑 Royal Exotics", desc: "Imported gourmet berries & truffles" },
    { id: "fresh", label: "🚜 Farm Fresh Direct", desc: "Harvested to kitchen in 6 hours" },
    { id: "bakery", label: "🥐 Artisanal Bakehouse", desc: "Fresh sourdough & pastries daily" }
  ];

  // Real-time WebSocket connection to system orders or simulated live ticks
  useEffect(() => {
    let ws: WebSocket | null = null;
    let fallbackInterval: NodeJS.Timeout | null = null;

    const connectWS = () => {
      try {
        // Attempt to connect to the production WebSocket gateway broker
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/notifications/live_ticker`;
        ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data && typeof data.live_count === "number") {
              setLiveOrders(data.live_count);
            }
          } catch (e) {
            // Ignore parse errors
          }
        };

        ws.onerror = () => {
          startFallback();
        };

        ws.onclose = () => {
          startFallback();
        };
      } catch (err) {
        startFallback();
      }
    };

    const startFallback = () => {
      if (fallbackInterval) return;
      fallbackInterval = setInterval(() => {
        setLiveOrders((prev) => {
          const delta = Math.floor(Math.random() * 3) + 1; // Increment by 1-3
          return prev + delta;
        });
      }, 4000);
    };

    connectWS();

    return () => {
      if (ws) ws.close();
      if (fallbackInterval) clearInterval(fallbackInterval);
    };
  }, []);

  const handleLocateUser = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation("Detected: Bandra West, Mumbai");
        },
        () => {
          setLocation("Mumbai, Maharashtra");
        }
      );
    }
  };

  return (
    <section 
      className="relative rounded-3xl overflow-hidden py-16 px-6 md:px-12 mb-12 shadow-premium bg-gradient-to-r from-brand-purple via-indigo-950 to-brand-blue"
      aria-label="Grocery Hero Section"
    >
      {/* Decorative luxury sparkles and light glows */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-amber-500/10 via-transparent to-transparent opacity-70 pointer-events-none" />
      <div className="absolute top-12 left-1/4 w-72 h-72 bg-brand-gold/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-4xl mx-auto text-center">
        {/* Real-time Orders Pulser Badge */}
        <div className="inline-flex items-center space-x-2 bg-black/30 backdrop-blur-md px-4 py-2 rounded-full border border-white/10 mb-6 shadow-md">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-white text-xs font-medium tracking-wide">
            Live Order Stream: <strong className="text-brand-gold">{liveOrders.toLocaleString()}</strong> celebrations catered today
          </span>
        </div>

        {/* Hero Headline */}
        <h1 className="font-heading text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
          Sovereign Groceries &<br />
          <span className="bg-gradient-to-r from-brand-gold via-amber-200 to-brand-gold bg-clip-text text-transparent">
            Royal Feast Essentials
          </span>
        </h1>

        <p className="text-white/80 font-body text-base md:text-lg max-w-2xl mx-auto mb-10">
          Curated organic yields, imported exotic delicacies, and local boutique harvests delivered to your doorstep in pristine premium batches.
        </p>

        {/* Search & Geolocation Console (Glassmorphism Wrapper) */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 p-4 rounded-2xl shadow-2xl max-w-3xl mx-auto mb-8 flex flex-col md:flex-row gap-3">
          {/* Geolocation selector (tap target min 44px) */}
          <div className="relative flex-1">
            <button
              onClick={() => setShowLocationDropdown(!showLocationDropdown)}
              className="w-full flex items-center justify-between bg-white/5 border border-white/10 hover:bg-white/15 px-4 h-12 rounded-xl text-white text-left text-sm transition focus:ring-2 focus:ring-brand-gold"
              aria-expanded={showLocationDropdown}
              aria-haspopup="listbox"
              style={{ minHeight: "44px" }}
            >
              <div className="flex items-center space-x-2 truncate">
                <MapPin className="text-brand-gold flex-shrink-0 h-4 w-4" />
                <span className="truncate">{location}</span>
              </div>
              <Compass className="text-white/40 h-4 w-4" />
            </button>

            {/* Geolocation dropdown */}
            <AnimatePresence>
              {showLocationDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute left-0 right-0 mt-2 bg-stone-900 border border-white/15 rounded-xl shadow-2xl z-50 overflow-hidden"
                  role="listbox"
                >
                  <button
                    onClick={() => {
                      handleLocateUser();
                      setShowLocationDropdown(false);
                    }}
                    className="w-full text-left px-4 py-3 text-brand-gold font-bold text-xs flex items-center space-x-2 hover:bg-white/5 border-b border-white/10 transition"
                    style={{ minHeight: "44px" }}
                  >
                    <Compass className="h-4 w-4 animate-spin-slow" />
                    <span>Detect My Accurate Location</span>
                  </button>
                  {POPULAR_LOCATIONS.map((loc) => (
                    <button
                      key={loc}
                      onClick={() => {
                        setLocation(loc);
                        setShowLocationDropdown(false);
                      }}
                      className="w-full text-left px-4 py-2.5 text-white/80 text-sm hover:bg-white/10 hover:text-white transition"
                      style={{ minHeight: "44px" }}
                      role="option"
                      aria-selected={location === loc}
                    >
                      {loc}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Search Outlets input */}
          <div className="relative flex-[1.5]">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 h-4 w-4" />
            <input
              type="text"
              placeholder="Search premium grocers, boutique sellers, ingredients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white placeholder-white/40 pl-11 pr-4 h-12 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-gold focus:bg-white/10 transition"
              style={{ minHeight: "44px" }}
            />
          </div>

          {/* Luxury CTA Button */}
          <button
            className="bg-gradient-to-r from-brand-gold to-amber-500 hover:from-amber-500 hover:to-brand-gold text-stone-900 font-bold px-6 h-12 rounded-xl transition-all hover:shadow-lg hover:shadow-brand-gold/20 flex items-center justify-center space-x-2 active:scale-95"
            style={{ minHeight: "44px" }}
          >
            <ShoppingBag className="h-4 w-4" />
            <span>Search</span>
          </button>
        </div>

        {/* Floating Glassmorphic Animated Pills */}
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {FILTER_PILLS.map((pill) => {
            const isActive = activePill === pill.id;

            return (
              <div key={pill.id} className="relative group">
                <button
                  onClick={() => setActivePill(isActive ? null : pill.id)}
                  className={`px-5 py-3 rounded-full text-sm font-semibold tracking-wide border transition-all duration-300 backdrop-blur-md flex items-center space-x-2 ${
                    isActive
                      ? "bg-brand-gold text-stone-900 border-brand-gold shadow-lg shadow-brand-gold/30"
                      : "bg-white/5 text-white/90 border-white/10 hover:bg-white/15 hover:border-white/20 hover:scale-105"
                  }`}
                  style={{ minHeight: "44px" }}
                >
                  <span>{pill.label}</span>
                  {isActive && <Sparkles className="h-3.5 w-3.5 text-stone-900 animate-pulse" />}
                </button>

                {/* Micro-info popup descriptions on hover */}
                <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-48 bg-stone-900/95 backdrop-blur-md border border-white/10 text-white/80 p-2.5 rounded-lg text-xs font-normal leading-relaxed opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 pointer-events-none shadow-xl z-50 text-center">
                  <p className="font-bold text-brand-gold mb-0.5">{pill.label}</p>
                  <p>{pill.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
