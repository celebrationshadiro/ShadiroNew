import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { admin } from '../../lib/api';
import { CreditCard, RefreshCw, Download, AlertTriangle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const normalizeStatus = (raw) => {
  const value = String(raw || '').toLowerCase();
  if (value === 'confirmed') return 'success';
  if (value === 'client_verified' || value === 'created') return 'pending';
  if (value === 'refunded') return 'refunded';
  if (value === 'failed') return 'failed';
  return value || 'pending';
};

const PaymentStatusBadge = ({ status }) => {
  const statusStyles = {
    pending: 'bg-amber-100 text-amber-800',
    success: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    refunded: 'bg-blue-100 text-blue-800',
  };
  const normalized = normalizeStatus(status);
  return <Badge className={statusStyles[normalized] || 'bg-stone-100'}>{normalized}</Badge>;
};

const extractPayload = (response) => response?.data?.data ?? response?.data ?? response;
const extractList = (response) => {
  const payload = extractPayload(response);
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.payments)) return payload.payments;
  return [];
};

const AdminPayments = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refundingId, setRefundingId] = useState(null);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(50);

  const loadPayments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await admin.getPayments({ skip, limit });
      setPayments(extractList(res));
    } catch (err) {
      console.error('Failed to load payments:', err);
      toast.error('Failed to load payments');
    } finally {
      setLoading(false);
    }
  }, [skip, limit]);

  useEffect(() => {
    loadPayments();
  }, [loadPayments]);

  const handleRefund = async (paymentId) => {
    const reason = prompt('Enter refund reason:');
    if (!reason) return;

    setRefundingId(paymentId);
    try {
      await admin.refundPayment(paymentId, reason);
      toast.success('Payment refunded successfully');
      loadPayments();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Refund failed');
    } finally {
      setRefundingId(null);
    }
  };

  const calculateStats = () => {
    const list = Array.isArray(payments) ? payments : [];
    const totalAmount = list.reduce((sum, p) => sum + ((p.amount || 0) / 100), 0);
    const successfulPayments = list.filter(p => normalizeStatus(p.status) === 'success').length;
    const failedPayments = list.filter(p => normalizeStatus(p.status) === 'failed').length;
    const refundedAmount = list
      .filter(p => normalizeStatus(p.status) === 'refunded')
      .reduce((sum, p) => sum + ((p.amount || 0) / 100), 0);

    return { totalAmount, successfulPayments, failedPayments, refundedAmount };
  };

  const stats = calculateStats();

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <CreditCard className="w-8 h-8" /> Payments Management
        </h1>
        <Button onClick={loadPayments} disabled={loading} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="p-4 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <p className="text-sm text-green-700 font-medium">Successful Payments</p>
          <p className="text-2xl font-bold text-green-900">{stats.successfulPayments}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <p className="text-sm text-blue-700 font-medium">Total Revenue</p>
          <p className="text-2xl font-bold text-blue-900">₹{stats.totalAmount.toLocaleString()}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <p className="text-sm text-red-700 font-medium">Failed Payments</p>
          <p className="text-2xl font-bold text-red-900">{stats.failedPayments}</p>
        </Card>
        <Card className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <p className="text-sm text-purple-700 font-medium">Refunded Amount</p>
          <p className="text-2xl font-bold text-purple-900">₹{stats.refundedAmount.toLocaleString()}</p>
        </Card>
      </div>

      {/* Payments List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
        </div>
      ) : payments.length === 0 ? (
        <Card className="p-8 text-center">
          <CreditCard className="w-12 h-12 mx-auto text-stone-300 mb-3" />
          <p className="text-stone-500">No payments found</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {payments.map((payment) => (
            <Card key={payment.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <CreditCard className="w-5 h-5 text-stone-400" />
                    <div>
                      <h3 className="font-semibold text-stone-900">
                        Payment #{payment.id.slice(0, 8)}
                      </h3>
                      <p className="text-sm text-stone-500">
                        Order: {payment.order_id?.slice(0, 8)} • User: {payment.user_id?.slice(0, 8)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-stone-600 mt-2">
                    <span>₹{payment.amount?.toLocaleString()}</span>
                    {payment.razorpay_payment_id && (
                      <span className="text-xs bg-stone-100 px-2 py-1 rounded text-stone-700">
                        RZP: {payment.razorpay_payment_id.slice(-8)}
                      </span>
                    )}
                    <span className="text-xs">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <PaymentStatusBadge status={payment.status} />

                  {normalizeStatus(payment.status) === 'success' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRefund(payment.id)}
                      disabled={refundingId === payment.id}
                      className="border-red-200 text-red-600 hover:bg-red-50"
                    >
                      {refundingId === payment.id ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin mr-1" /> Refunding
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-4 h-4 mr-1" /> Refund
                        </>
                      )}
                    </Button>
                  )}

                  {normalizeStatus(payment.status) === 'refunded' && (
                    <span className="text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded font-medium">
                      ID: {payment.refund_id?.slice(-8)}
                    </span>
                  )}
                </div>
              </div>

              {payment.refund_reason && (
                <div className="mt-2 text-xs text-stone-500 bg-stone-50 p-2 rounded">
                  Refund Reason: {payment.refund_reason}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && payments.length > 0 && (
        <div className="flex items-center justify-between mt-6">
          <Button
            onClick={() => setSkip(Math.max(0, skip - limit))}
            disabled={skip === 0}
            variant="outline"
            size="sm"
          >
            Previous
          </Button>
          <span className="text-sm text-stone-600">
            Showing {skip + 1} - {skip + payments.length}
          </span>
          <Button
            onClick={() => setSkip(skip + limit)}
            disabled={payments.length < limit}
            variant="outline"
            size="sm"
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};

export default AdminPayments;
