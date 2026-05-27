import React, { useState, useEffect } from 'react';
import { bookingsApi } from '../../lib/api';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { AlertTriangle, CheckCircle, Clock, User, Phone, MapPin, TrendingUp, MoreVertical } from 'lucide-react';
import { toast } from 'sonner';
import '../../styles/AdminEmergency.css';

const AdminEmergencyDashboard = () => {
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    resolved: 0,
    avgResolutionTime: 0,
    replacementSuccessRate: 0,
  });
  const [selectedEmergency, setSelectedEmergency] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [actionReason, setActionReason] = useState('');
  const [activeAction, setActiveAction] = useState(null);

  useEffect(() => {
    loadEmergencies();
  }, []);

  const loadEmergencies = async () => {
    setLoading(true);
    try {
      const response = await bookingsApi.getEmergencyBookings?.();
      const data = response?.data || [];
      setEmergencies(data);
      calculateStats(data);
    } catch (error) {
      console.error('Failed to load emergencies:', error);
      toast.error('Failed to load emergency bookings');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (data) => {
    const total = data.length;
    const pending = data.filter(e => e.status === 'pending').length;
    const resolved = data.filter(e => e.status === 'resolved').length;

    // Calculate average resolution time
    let totalResolutionTime = 0;
    let resolvedCount = 0;
    data.forEach(e => {
      if (e.resolved_at && e.created_at) {
        totalResolutionTime += new Date(e.resolved_at) - new Date(e.created_at);
        resolvedCount++;
      }
    });
    const avgResolutionTime = resolvedCount > 0 ? Math.round(totalResolutionTime / resolvedCount / 60000) : 0;

    // Calculate replacement success rate
    const withReplacement = data.filter(e => e.replacement_accepted).length;
    const replacementSuccessRate = total > 0 ? Math.round((withReplacement / total) * 100) : 0;

    setStats({
      total,
      pending,
      resolved,
      avgResolutionTime,
      replacementSuccessRate,
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-amber-50 text-amber-900 border-amber-200';
      case 'resolved':
        return 'bg-green-50 text-green-900 border-green-200';
      case 'escalated':
        return 'bg-red-50 text-red-900 border-red-200';
      default:
        return 'bg-stone-50 text-stone-900 border-stone-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-5 h-5" />;
      case 'resolved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'escalated':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const handleApproveReplacement = async (emergencyId) => {
    try {
      await bookingsApi.approveEmergencyReplacement?.(emergencyId);
      toast.success('Replacement approved');
      loadEmergencies();
      setShowDetailsModal(false);
    } catch (error) {
      toast.error('Failed to approve replacement');
    }
  };

  const handleInitiateRefund = async (emergencyId) => {
    try {
      await bookingsApi.initiateRefund?.(emergencyId);
      toast.success('Refund initiated');
      loadEmergencies();
      setShowDetailsModal(false);
    } catch (error) {
      toast.error('Failed to initiate refund');
    }
  };

  const handleEscalate = async (emergencyId) => {
    if (!actionReason.trim()) {
      toast.error('Please provide a reason');
      return;
    }
    try {
      await bookingsApi.escalateEmergency?.(emergencyId, actionReason);
      toast.success('Emergency escalated');
      loadEmergencies();
      setShowDetailsModal(false);
      setActionReason('');
    } catch (error) {
      toast.error('Failed to escalate');
    }
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const timeSince = (date) => {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-stone-600">Loading emergencies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-stone-900 mb-2">Emergency Cancellations</h1>
        <p className="text-stone-600">Manage and resolve vendor emergency cancellations</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="bg-white border-stone-200">
          <div className="p-6">
            <p className="text-sm font-medium text-stone-600 mb-2">Total Emergencies</p>
            <p className="text-3xl font-bold text-stone-900">{stats.total}</p>
            <p className="text-xs text-stone-500 mt-2">All time</p>
          </div>
        </Card>

        <Card className="bg-amber-50 border-amber-200">
          <div className="p-6">
            <p className="text-sm font-medium text-amber-900 mb-2">Pending</p>
            <p className="text-3xl font-bold text-amber-900">{stats.pending}</p>
            <p className="text-xs text-amber-700 mt-2">Awaiting action</p>
          </div>
        </Card>

        <Card className="bg-green-50 border-green-200">
          <div className="p-6">
            <p className="text-sm font-medium text-green-900 mb-2">Resolved</p>
            <p className="text-3xl font-bold text-green-900">{stats.resolved}</p>
            <p className="text-xs text-green-700 mt-2">{stats.replacementSuccessRate}% replacement success</p>
          </div>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <div className="p-6">
            <p className="text-sm font-medium text-blue-900 mb-2">Avg Resolution</p>
            <p className="text-3xl font-bold text-blue-900">{stats.avgResolutionTime}</p>
            <p className="text-xs text-blue-700 mt-2">Minutes</p>
          </div>
        </Card>

        <Card className="bg-purple-50 border-purple-200">
          <div className="p-6">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-purple-900" />
              <p className="text-sm font-medium text-purple-900">Success Rate</p>
            </div>
            <p className="text-3xl font-bold text-purple-900">{stats.replacementSuccessRate}%</p>
            <p className="text-xs text-purple-700 mt-2">Replacement accepted</p>
          </div>
        </Card>
      </div>

      {/* Emergency List */}
      {emergencies.length === 0 ? (
        <Card className="bg-white border-stone-200 p-12 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-stone-900 mb-2">No Emergencies</h3>
          <p className="text-stone-600">Great! All bookings are running smoothly.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {emergencies.map((emergency) => (
            <Card
              key={emergency.id}
              className={`border-2 transition-all hover:shadow-lg ${getStatusColor(emergency.status)}`}
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-4">
                      {getStatusIcon(emergency.status)}
                      <div>
                        <h3 className="font-semibold text-lg">
                          Booking #{emergency.booking_id?.slice(0, 8)}
                        </h3>
                        <p className="text-sm opacity-75">{timeSince(emergency.created_at)}</p>
                      </div>
                    </div>

                    {/* Vendor & Customer Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-xs font-medium opacity-75 mb-1">Vendor</p>
                        <p className="font-medium">{emergency.vendor_name}</p>
                        <p className="text-sm opacity-75">{emergency.vendor_category}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium opacity-75 mb-1">Customer</p>
                        <p className="font-medium flex items-center gap-2">
                          <User className="w-4 h-4" />
                          {emergency.customer_name}
                        </p>
                        {emergency.customer_phone && (
                          <p className="text-sm opacity-75 flex items-center gap-2">
                            <Phone className="w-4 h-4" />
                            {emergency.customer_phone}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Event Details */}
                    {emergency.event_date && (
                      <div className="mb-4 p-4 bg-stone-100/50 rounded-lg">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <p className="text-xs font-medium opacity-75 mb-1">Event Date</p>
                            <p className="font-medium">{formatTime(emergency.event_date)}</p>
                          </div>
                          {emergency.event_location && (
                            <div>
                              <p className="text-xs font-medium opacity-75 mb-1">Location</p>
                              <p className="font-medium flex items-center gap-2">
                                <MapPin className="w-4 h-4" />
                                {emergency.event_location}
                              </p>
                            </div>
                          )}
                          {emergency.booking_amount && (
                            <div>
                              <p className="text-xs font-medium opacity-75 mb-1">Booking Amount</p>
                              <p className="font-medium">₹{emergency.booking_amount?.toLocaleString()}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Cancellation Reason */}
                    {emergency.reason && (
                      <div className="mb-4 p-4 bg-red-50/30 rounded-lg border border-red-200/30">
                        <p className="text-xs font-medium opacity-75 mb-1">Cancellation Reason</p>
                        <p className="text-sm">{emergency.reason}</p>
                      </div>
                    )}

                    {/* Status & Replacements */}
                    <div className="flex items-center gap-4 text-sm">
                      <div>
                        <p className="opacity-75 text-xs mb-1">Status</p>
                        <p className="font-medium capitalize">{emergency.status}</p>
                      </div>
                      {emergency.replacement_vendors && (
                        <div>
                          <p className="opacity-75 text-xs mb-1">Replacements</p>
                          <p className="font-medium">{emergency.replacement_vendors.length} offered</p>
                        </div>
                      )}
                      {emergency.replacement_accepted !== undefined && (
                        <div>
                          <p className="opacity-75 text-xs mb-1">Replacement Status</p>
                          <p className="font-medium">
                            {emergency.replacement_accepted ? '✓ Accepted' : '✗ Not accepted'}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Button */}
                  <Button
                    size="sm"
                    className="ml-4 bg-primary hover:bg-primary/90 text-white"
                    onClick={() => {
                      setSelectedEmergency(emergency);
                      setShowDetailsModal(true);
                    }}
                  >
                    <MoreVertical className="w-4 h-4" />
                    Manage
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Details Modal */}
      {showDetailsModal && selectedEmergency && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full bg-white border-0 shadow-2xl rounded-2xl">
            <div className="p-8">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-stone-900">Emergency Management</h2>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-stone-400 hover:text-stone-600 text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Details */}
              <div className="space-y-6 mb-8">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-xs font-medium text-stone-600 mb-2">Booking ID</p>
                    <p className="font-semibold text-stone-900">{selectedEmergency.booking_id?.slice(0, 12)}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-stone-600 mb-2">Status</p>
                    <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedEmergency.status)}`}>
                      {selectedEmergency.status}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-stone-600 mb-2">Vendor</p>
                    <p className="font-semibold text-stone-900">{selectedEmergency.vendor_name}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-stone-600 mb-2">Customer</p>
                    <p className="font-semibold text-stone-900">{selectedEmergency.customer_name}</p>
                  </div>
                </div>

                {selectedEmergency.reason && (
                  <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <p className="text-xs font-medium text-red-900 mb-2">Cancellation Reason</p>
                    <p className="text-sm text-red-800">{selectedEmergency.reason}</p>
                  </div>
                )}

                {selectedEmergency.replacement_vendors && selectedEmergency.replacement_vendors.length > 0 && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-xs font-medium text-blue-900 mb-3">Replacement Vendors Offered</p>
                    <div className="space-y-2">
                      {selectedEmergency.replacement_vendors.map((vendor, idx) => (
                        <div key={idx} className="text-sm">
                          <p className="font-medium text-blue-900">{vendor.name}</p>
                          <p className="text-blue-700">Rating: {vendor.rating || 'N/A'} ⭐</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                {selectedEmergency.status === 'pending' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-stone-700 mb-2">
                        Action Reason (optional)
                      </label>
                      <textarea
                        value={actionReason}
                        onChange={(e) => setActionReason(e.target.value)}
                        placeholder="Add notes for this action..."
                        className="w-full px-4 py-2 border border-stone-300 rounded-lg text-sm"
                        rows="3"
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <Button
                        onClick={() => handleApproveReplacement(selectedEmergency.id)}
                        className="bg-green-500 hover:bg-green-600 text-white"
                      >
                        Approve Replacement
                      </Button>
                      <Button
                        onClick={() => handleInitiateRefund(selectedEmergency.id)}
                        className="bg-blue-500 hover:bg-blue-600 text-white"
                      >
                        Initiate Refund
                      </Button>
                      <Button
                        onClick={() => handleEscalate(selectedEmergency.id)}
                        className="bg-red-500 hover:bg-red-600 text-white"
                      >
                        Escalate
                      </Button>
                    </div>
                  </>
                )}

                {selectedEmergency.status !== 'pending' && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200 text-center">
                    <p className="text-green-900 font-medium">✓ This emergency has been resolved</p>
                  </div>
                )}

                <Button
                  variant="outline"
                  className="w-full border-stone-300 text-stone-700"
                  onClick={() => setShowDetailsModal(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AdminEmergencyDashboard;
