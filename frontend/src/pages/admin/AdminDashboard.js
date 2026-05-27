import React, { useState, useEffect } from 'react';
import { Card } from '../../components/ui/card';
import {
  Users,
  Store,
  Clock,
  TrendingUp,
  Calendar,
  ShoppingBag,
  Briefcase,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { admin } from '../../lib/api';
import CategoryBadge from '../../components/CategoryBadge';

const StatCard = ({ icon: Icon, label, value, subtext }) => (
  <Card className="p-6 bg-white rounded-2xl border border-stone-100 shadow-sm">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-stone-500 text-sm font-medium">{label}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        {subtext && <p className="text-stone-400 text-xs mt-1">{subtext}</p>}
      </div>
      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
        <Icon className="w-6 h-6 text-primary" />
      </div>
    </div>
  </Card>
);

const AdminDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [pricingInsights, setPricingInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [analyticsRes, pricingRes] = await Promise.all([
        admin.getAnalytics(),
        admin.getPricingInsights(),
      ]);
      setAnalytics(analyticsRes.data);
      setPricingInsights(pricingRes.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="h-8 w-48 bg-stone-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-white border border-stone-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const kpi = (path, fallback = 0) => {
    try {
      return path.split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), analytics) ?? fallback;
    } catch (e) {
      return fallback;
    }
  };

  const revenueSplit = {
    grocery: kpi('revenue_grocery', analytics?.revenue_split?.grocery ?? 0),
    services: kpi('revenue_services', analytics?.revenue_split?.services ?? 0),
  };

  const categoryCounts = analytics?.category_demand || analytics?.category_breakdown || [];
  const verificationPending = kpi('pending_vendor_approvals', 0);
  const lowCompletion = kpi('low_completion_vendors', analytics?.profile_completion_lt_80 || 0);
  const failRate = (() => {
    const failed = kpi('service_failures', analytics?.service_failures || 0);
    const total = kpi('service_bookings_month', analytics?.service_bookings_month || 0) || 0;
    if (!total) return 0;
    return Math.round((failed / total) * 100);
  })();
  const riskyVendors = analytics?.risky_vendors || [];
  const demandHeat = analytics?.category_fail_rate || analytics?.category_demand || [];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <StatCard icon={Users} label="Total Users" value={analytics?.total_users ?? 0} />
        <StatCard icon={Store} label="Total Vendors" value={analytics?.total_vendors ?? 0} subtext="All categories" />
        <StatCard icon={Clock} label="Pending Approvals" value={verificationPending} subtext="Awaiting review" />
        <StatCard icon={ShoppingBag} label="Grocery Orders" value={kpi('grocery_orders_today', 0)} subtext={`Today · ${kpi('grocery_orders_month', 0)} this month`} />
        <StatCard icon={Briefcase} label="Service Bookings" value={kpi('service_bookings_today', 0)} subtext={`Today · ${kpi('service_bookings_month', 0)} this month`} />
        <StatCard icon={AlertTriangle} label="Service Fail Rate" value={`${failRate}%`} subtext="This month" />
        <StatCard icon={ShieldCheck} label="Verification Pending" value={verificationPending} subtext="Vendor documents" />
        <StatCard icon={TrendingUp} label="Revenue (Grocery)" value={`₹${revenueSplit.grocery.toLocaleString()}`} subtext="Split" />
        <StatCard icon={TrendingUp} label="Revenue (Services)" value={`₹${revenueSplit.services.toLocaleString()}`} subtext="Split" />
        <StatCard icon={TrendingUp} label="Revenue Split" value={`₹${(revenueSplit.grocery + revenueSplit.services).toLocaleString()}`} subtext={`Grocery ₹${revenueSplit.grocery.toLocaleString()} · Services ₹${revenueSplit.services.toLocaleString()}`} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard icon={ShieldCheck} label="Verification Pending" value={verificationPending} subtext="Vendors waiting on KYC" />
        <StatCard icon={AlertTriangle} label="Profile < 80%" value={lowCompletion} subtext="Needs completion" />
        <Card className="p-6 bg-white rounded-2xl border border-stone-100 shadow-sm">
          <p className="text-stone-500 text-sm font-medium mb-3">Vendors by Category</p>
          <div className="flex flex-wrap gap-2">
            {categoryCounts.length === 0 && <span className="text-stone-500 text-sm">No data yet.</span>}
            {categoryCounts.map((c) => (
              <div key={c.category || c.slug} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-stone-50 border border-stone-100">
                <CategoryBadge slug={c.category || c.slug} />
                <span className="text-sm font-semibold">{c.count || c.total || 0}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-6 bg-white rounded-2xl border border-stone-100 shadow-sm">
          <p className="text-stone-500 text-sm font-medium mb-3">Category Health (fail rate)</p>
          {(analytics?.category_fail_rate && Object.keys(analytics.category_fail_rate).length > 0) ? (
            <div className="space-y-2">
              {Object.entries(analytics.category_fail_rate).map(([cat, rate]) => (
                <div key={cat} className="flex items-center justify-between text-sm">
                  <CategoryBadge slug={cat} />
                  <span className={`font-semibold ${rate > 0.2 ? 'text-red-600' : 'text-stone-800'}`}>
                    {(rate * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-stone-500 text-sm">No fail-rate data available.</p>
          )}
        </Card>
        <Card className="p-6 bg-white rounded-2xl border border-stone-100 shadow-sm">
          <p className="text-stone-500 text-sm font-medium mb-3">Risky Vendors</p>
          {Array.isArray(analytics?.risky_vendors) && analytics.risky_vendors.length > 0 ? (
            <div className="space-y-2">
              {analytics.risky_vendors.slice(0, 5).map((v) => (
                <div key={v.id} className="flex items-center justify-between text-sm">
                  <span className="text-stone-700">{v.business_name || 'Vendor'}</span>
                  <span className="text-amber-700 font-semibold">Risk {v.risk_score ?? '—'}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-stone-500 text-sm">No risky vendors flagged.</p>
          )}
        </Card>
        <Card className="p-6 bg-white rounded-2xl border border-stone-100 shadow-sm">
          <p className="text-stone-500 text-sm font-medium mb-3">Demand Heat (by city)</p>
          {Array.isArray(analytics?.demand_heat) && analytics.demand_heat.length > 0 ? (
            <div className="space-y-2">
              {analytics.demand_heat.slice(0, 6).map((d) => (
                <div key={d.city} className="flex items-center justify-between text-sm">
                  <span className="text-stone-700">{d.city}</span>
                  <span className="font-semibold text-primary">{d.count || d.demand}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-stone-500 text-sm">No demand data yet.</p>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="p-6 bg-white rounded-2xl border border-stone-100">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5" /> Monthly Bookings
          </h2>
          {analytics?.monthly_bookings?.length > 0 ? (
            <div className="space-y-3">
              {analytics.monthly_bookings.slice(-6).map((m) => (
                <div key={m.month} className="flex justify-between items-center">
                  <span className="text-stone-600">{m.month}</span>
                  <span className="font-semibold">{m.count} bookings</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-stone-500">No booking data yet.</p>
          )}
        </Card>

        <Card className="p-6 bg-white rounded-2xl border border-stone-100">
          <h2 className="text-lg font-semibold mb-4">Pricing Insights</h2>
          {pricingInsights ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-stone-600">Avg Base Price</span>
                <span className="font-semibold">₹{(pricingInsights.avg_base_price || 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-stone-600">Vendors With Rules</span>
                <span className="font-semibold">{pricingInsights.vendors_with_pricing_rules}</span>
              </div>
              <div className="pt-2">
                <p className="text-sm text-stone-500 mb-2">Category Rule Coverage</p>
                {Object.entries(pricingInsights.category_rule_coverage || {}).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(pricingInsights.category_rule_coverage).map(([category, count]) => (
                      <div key={category} className="flex justify-between items-center text-sm">
                        <span className="text-stone-600">{category}</span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-stone-500 text-sm">No pricing rules configured.</p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-stone-500">No pricing data yet.</p>
          )}
        </Card>

        <Card className="p-6 bg-white rounded-2xl border border-stone-100">
          <h2 className="text-lg font-semibold mb-4">Category Demand</h2>
          {analytics?.category_demand?.length > 0 ? (
            <div className="space-y-3">
              {analytics.category_demand.map((c) => (
                <div key={c.category} className="flex justify-between items-center">
                  <span className="text-stone-600">{c.category}</span>
                  <span className="font-semibold">{c.count} vendors</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-stone-500">No category data yet.</p>
          )}
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
