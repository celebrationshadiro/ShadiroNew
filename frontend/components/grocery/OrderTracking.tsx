"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Clock, Truck, ShieldAlert, Sparkles, MapPin, Phone } from "lucide-react";
import confetti from "canvas-confetti";

type DeliveryStatus = "ORDER_PLACED" | "ORDER_CONFIRMED" | "OUT_FOR_DELIVERY" | "DELIVERED";

interface OrderTrackingProps {
  orderId: string;
  userId: string;
  onClose?: () => void;
}

export default function OrderTracking({ orderId, userId, onClose }: OrderTrackingProps) {
  const [status, setStatus] = useState<DeliveryStatus>("ORDER_PLACED");
  const [isConnected, setIsConnected] = useState(false);
  const [eta, setEta] = useState("35-40 mins");

  const stages: { key: DeliveryStatus; label: string; desc: string; icon: React.ReactNode }[] = [
    {
      key: "ORDER_PLACED",
      label: "Order Placed",
      desc: "We have received your royal order details",
      icon: <Clock className="h-5 w-5" />,
    },
    {
      key: "ORDER_CONFIRMED",
      label: "Order Confirmed",
      desc: "Our verified premium merchants have packaged your box",
      icon: <CheckCircle2 className="h-5 w-5" />,
    },
    {
      key: "OUT_FOR_DELIVERY",
      label: "Out for Delivery",
      desc: "Our trusted delivery executive is en route to you",
      icon: <Truck className="h-5 w-5" />,
    },
    {
      key: "DELIVERED",
      label: "Delivered",
      desc: "Celebrations complete! Delivered to your doorstep",
      icon: <Sparkles className="h-5 w-5" />,
    },
  ];

  // Helper to trigger confetti celebration
  const triggerConfetti = () => {
    const duration = 4 * 1000;
    const end = Date.now() + duration;

    const frame = () => {
      confetti({
        particleCount: 4,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ["#D4AF37", "#097969", "#2C5285"],
      });
      confetti({
        particleCount: 4,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ["#D4AF37", "#097969", "#2C5285"],
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    };
    frame();
  };

  // Real-time WebSocket connection to Redis WebSocket Broker
  useEffect(() => {
    let ws: WebSocket | null = null;
    let fallbackTimeout: NodeJS.Timeout | null = null;

    const connectWS = () => {
      try {
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        // Connect to distributed broker notification endpoint
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/delivery/${userId}`;
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload && payload.order_id === orderId && payload.status) {
              const newStatus = payload.status as DeliveryStatus;
              setStatus(newStatus);
              if (payload.eta) setEta(payload.eta);

              if (newStatus === "DELIVERED") {
                triggerConfetti();
              }
            }
          } catch (err) {
            // Ignore format errors
          }
        };

        ws.onerror = () => {
          setIsConnected(false);
          startFallbackSimulation();
        };

        ws.onclose = () => {
          setIsConnected(false);
          startFallbackSimulation();
        };
      } catch (err) {
        startFallbackSimulation();
      }
    };

    // Graceful fallback simulation if connection fails
    const startFallbackSimulation = () => {
      let currentStageIndex = 0;
      const progressSimulation = () => {
        fallbackTimeout = setTimeout(() => {
          if (currentStageIndex < stages.length - 1) {
            currentStageIndex += 1;
            const nextStatus = stages[currentStageIndex].key;
            setStatus(nextStatus);

            if (nextStatus === "OUT_FOR_DELIVERY") setEta("10-15 mins");
            if (nextStatus === "DELIVERED") {
              setEta("0 mins");
              triggerConfetti();
            } else {
              progressSimulation();
            }
          }
        }, 12000); // Transition stage every 12 seconds
      };
      progressSimulation();
    };

    connectWS();

    return () => {
      if (ws) ws.close();
      if (fallbackTimeout) clearTimeout(fallbackTimeout);
    };
  }, [orderId, userId]);

  // Determine stage completion index
  const activeIndex = stages.findIndex((s) => s.key === status);

  return (
    <div 
      className="bg-white border border-stone-200 rounded-3xl p-6 md:p-8 max-w-2xl mx-auto shadow-2xl relative overflow-hidden"
      role="region"
      aria-label="Order Tracking Console"
    >
      {/* Decorative luxury gold ambient glow */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-brand-gold/5 rounded-full blur-2xl pointer-events-none" />

      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-stone-100 gap-4">
        <div>
          <span className="text-[10px] font-bold text-stone-400 uppercase tracking-widest block mb-1">
            Real-Time Tracking Panel
          </span>
          <h2 className="font-heading text-2xl font-bold text-stone-900 flex items-center gap-2">
            Order #{orderId.slice(-8).toUpperCase()}{" "}
            <span className="bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/20 text-xs px-2.5 py-0.5 rounded-full font-sans font-bold">
              Active Delivery
            </span>
          </h2>
        </div>

        {/* Live indicators */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
            <span className="font-bold text-stone-600">
              {isConnected ? "Live Socket Link" : "Auto Simulation Mode"}
            </span>
          </div>
          <div className="bg-stone-50 border border-stone-200 px-3 py-1.5 rounded-lg text-stone-700 font-bold">
            ETA: <span className="text-brand-emerald">{eta}</span>
          </div>
        </div>
      </div>

      {/* Live Timeline Graphics */}
      <div className="py-8 space-y-6 relative">
        {/* Central connecting bar */}
        <div className="absolute left-[21px] top-10 bottom-10 w-1 bg-stone-100 -z-10" />

        {/* Dynamic completed bar */}
        <motion.div
          className="absolute left-[21px] top-10 w-1 bg-gradient-to-b from-brand-emerald via-brand-gold to-brand-blue -z-10 origin-top"
          initial={{ scaleY: 0 }}
          animate={{ scaleY: activeIndex / (stages.length - 1) }}
          transition={{ duration: 1 }}
          style={{ bottom: "40px" }}
        />

        <div className="space-y-8">
          {stages.map((stage, idx) => {
            const isCompleted = idx < activeIndex;
            const isActive = idx === activeIndex;
            const isPending = idx > activeIndex;

            return (
              <div 
                key={stage.key}
                className="flex items-start space-x-4 group"
              >
                {/* Node Indicators */}
                <motion.div
                  className={`flex h-11 w-11 items-center justify-center rounded-full border-2 z-10 transition-colors duration-300 ${
                    isCompleted
                      ? "bg-brand-emerald border-brand-emerald text-white shadow-md shadow-brand-emerald/20"
                      : isActive
                      ? "bg-white border-brand-gold text-brand-gold shadow-lg shadow-brand-gold/30 animate-pulseScale"
                      : "bg-white border-stone-200 text-stone-400"
                  }`}
                  whileHover={{ scale: 1.05 }}
                  aria-hidden="true"
                >
                  {stage.icon}
                </motion.div>

                {/* Text stage details */}
                <div className="flex-1 pt-1.5">
                  <div className="flex items-center justify-between">
                    <h3 className={`font-bold text-sm md:text-base ${
                      isActive ? "text-brand-gold-dark" : isCompleted ? "text-stone-800" : "text-stone-400"
                    }`}>
                      {stage.label}
                    </h3>
                    {isActive && (
                      <span className="text-[10px] font-bold tracking-widest text-brand-gold-dark uppercase animate-pulse">
                        Active Step
                      </span>
                    )}
                  </div>
                  <p className={`text-xs mt-0.5 ${
                    isPending ? "text-stone-400" : "text-stone-500"
                  }`}>
                    {stage.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Delivery Executive Info Overlay (Active when Out for Delivery) */}
      <AnimatePresence>
        {activeIndex >= 2 && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            className="bg-stone-50 border border-stone-200 rounded-2xl p-4.5 mb-6 flex items-center justify-between shadow-sm"
          >
            <div className="flex items-center space-x-3.5">
              <div className="h-11 w-11 rounded-full bg-brand-gold/10 border border-brand-gold/20 flex items-center justify-center font-bold text-brand-gold-dark">
                👨🏽‍✈️
              </div>
              <div>
                <p className="text-xs text-stone-400 font-bold uppercase tracking-wider">Your Executive</p>
                <p className="font-bold text-sm text-stone-850">Vikram Singh</p>
                <p className="text-xs text-stone-500 flex items-center gap-1">
                  <MapPin className="h-3 w-3 text-stone-400" /> 1.2 km away (Royal Delights Batch)
                </p>
              </div>
            </div>

            {/* Quick dial button (tap target min 44px) */}
            <a
              href="tel:+919999999999"
              className="bg-white border border-stone-200 hover:border-brand-emerald text-stone-700 hover:text-brand-emerald rounded-full p-3.5 transition flex items-center justify-center shadow-sm"
              style={{ width: "44px", height: "44px" }}
              aria-label="Call delivery executive"
            >
              <Phone className="h-4.5 w-4.5" />
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Close button at bottom */}
      {onClose && (
        <button
          onClick={onClose}
          className="w-full bg-stone-900 hover:bg-stone-800 text-white font-bold h-11 rounded-xl transition active:scale-98 shadow-md"
          style={{ minHeight: "44px" }}
        >
          Close Panel
        </button>
      )}
    </div>
  );
}
