'use client';

import React, { useEffect, useState } from 'react';

export default function UserDashboard() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Client-side authentication lookup logic
    const fetchSession = async () => {
      try {
        const stored = localStorage.getItem('shadiro_user');
        if (stored) {
          setUser(JSON.parse(stored));
        }
      } catch (e) {
        console.error('Failed to parse client authentication session:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchSession();
  }, []);

  if (loading) {
    return (
      <div className="flex-grow flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-pink-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 flex-grow w-full">
      <div className="bg-white border border-stone-200 rounded-2xl p-6 md:p-10 shadow-sm max-w-4xl mx-auto">
        <h1 className="font-serif text-3xl font-bold text-stone-900 mb-6">Welcome Back, {user?.name || 'Guest'}</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <div className="border border-stone-150 rounded-xl p-5 hover:border-pink-500 transition duration-300">
            <span className="text-xl mb-2 block">📅</span>
            <h3 className="font-serif text-lg font-bold mb-2">My Bookings</h3>
            <p className="text-stone-500 text-sm">Track your scheduled event setups, planners verification checklist, and escrow payouts.</p>
          </div>

          <div className="border border-stone-150 rounded-xl p-5 hover:border-pink-500 transition duration-300">
            <span className="text-xl mb-2 block">🛒</span>
            <h3 className="font-serif text-lg font-bold mb-2">Grocery Orders</h3>
            <p className="text-stone-500 text-sm">View suborder logs, active delivery routes, and dynamic slot selections.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
