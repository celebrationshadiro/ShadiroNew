import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { admin } from '../../lib/api';
import { TrendingUp, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const AdminReport = () => {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('acceptance_rate');

  const loadReport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await admin.getVendorReliabilityReport({ skip: 0, limit: 500 });
      setVendors(res.data.vendors || []);
    } catch (err) {
      console.error('Failed to load report:', err);
      toast.error('Failed to load reliability report');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const sortedVendors = [...vendors].sort((a, b) => {
    if (sortBy === 'acceptance_rate') {
      return (b.acceptance_rate || 0) - (a.acceptance_rate || 0);
    } else if (sortBy === 'emergency_count') {
      return (a.emergency_count || 0) - (b.emergency_count || 0);
    } else if (sortBy === 'completed_count') {
      return (b.completed_count || 0) - (a.completed_count || 0);
    }
    return 0;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Vendor Reliability Report</h1>
      <p className="text-stone-600 mb-6">Monitor vendor metrics and quality indicators</p>

      {/* Sort Controls */}
      <div className="flex gap-2 mb-6 flex-wrap">
        <label className="text-sm text-stone-600 flex items-center">
          Sort by:
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="ml-2 px-3 py-1 border border-stone-300 rounded text-sm"
          >
            <option value="acceptance_rate">Acceptance Rate (High→Low)</option>
            <option value="emergency_count">Emergency Count (Low→High)</option>
            <option value="completed_count">Completed Bookings (High→Low)</option>
          </select>
        </label>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100">
          <p className="text-xs text-green-600 uppercase font-semibold">Total Vendors</p>
          <p className="text-3xl font-bold text-green-900">{vendors.length}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100">
          <p className="text-xs text-blue-600 uppercase font-semibold">Avg Acceptance Rate</p>
          <p className="text-3xl font-bold text-blue-900">
            {vendors.length > 0
              ? Math.round(
                  (vendors.reduce((s, v) => s + (v.acceptance_rate || 0), 0) / vendors.length) * 100
                )
              : 0}
            %
          </p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-100">
          <p className="text-xs text-amber-600 uppercase font-semibold">Total Completed</p>
          <p className="text-3xl font-bold text-amber-900">
            {vendors.reduce((s, v) => s + (v.completed_count || 0), 0)}
          </p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-red-50 to-rose-50 border border-red-100">
          <p className="text-xs text-red-600 uppercase font-semibold">Total Emergencies</p>
          <p className="text-3xl font-bold text-red-900">
            {vendors.reduce((s, v) => s + (v.emergency_count || 0), 0)}
          </p>
        </Card>
      </div>

      {/* Vendors Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-stone-100 border-b border-stone-300">
                <th className="text-left px-4 py-2 font-semibold text-stone-700">Business Name</th>
                <th className="text-left px-4 py-2 font-semibold text-stone-700">City</th>
                <th className="text-center px-4 py-2 font-semibold text-stone-700">Acceptance Rate</th>
                <th className="text-center px-4 py-2 font-semibold text-stone-700">Accepted</th>
                <th className="text-center px-4 py-2 font-semibold text-stone-700">Completed</th>
                <th className="text-center px-4 py-2 font-semibold text-stone-700">Rejected</th>
                <th className="text-center px-4 py-2 font-semibold text-stone-700">Emergency</th>
              </tr>
            </thead>
            <tbody>
              {sortedVendors.map((v) => {
                const acceptanceRate = v.acceptance_rate || 0;
                const accepted = v.accepted_count || 0;
                const completed = v.completed_count || 0;
                const rejected = v.rejected_count || 0;
                const emergency = v.emergency_count || 0;

                const getRateColor = (rate) => {
                  if (rate >= 0.8) return 'bg-green-100 text-green-800';
                  if (rate >= 0.6) return 'bg-yellow-100 text-yellow-800';
                  return 'bg-red-100 text-red-800';
                };

                const getEmergencyColor = (count) => {
                  if (count === 0) return 'bg-green-100 text-green-800';
                  if (count <= 2) return 'bg-yellow-100 text-yellow-800';
                  return 'bg-red-100 text-red-800';
                };

                return (
                  <tr key={v.id} className="border-b border-stone-200 hover:bg-stone-50">
                    <td className="px-4 py-3 font-medium text-stone-900">{v.business_name}</td>
                    <td className="px-4 py-3 text-stone-600">{v.city || 'N/A'}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge className={getRateColor(acceptanceRate)}>
                        {Math.round(acceptanceRate * 100)}%
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant="outline">{accepted}</Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant="outline" className="bg-green-50 border-green-200 text-green-700">
                        {completed}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant="outline" className="bg-red-50 border-red-200 text-red-700">
                        {rejected}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge className={getEmergencyColor(emergency)}>{emergency}</Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminReport;
