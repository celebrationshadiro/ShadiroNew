import React, { useCallback, useEffect, useState } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { admin } from '../../lib/api';
import { Loader2, RefreshCw, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const StatusBadge = ({ status }) => {
  const styles = {
    pending: 'bg-amber-100 text-amber-800',
    completed: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  };
  return <Badge className={styles[status] || 'bg-stone-100'}>{status}</Badge>;
};

const AdminPayouts = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await admin.getPayoutRequests();
      const raw = res?.data;
      const list = Array.isArray(raw)
        ? raw
        : Array.isArray(raw?.items)
          ? raw.items
          : [];
      setRequests(list);
    } catch (err) {
      console.error('Failed to load payout requests:', err);
      toast.error('Failed to load payout requests');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const handleApprove = async (id) => {
    setActioningId(id);
    try {
      await admin.approvePayout(id);
      toast.success('Payout approved');
      loadRequests();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve payout');
    } finally {
      setActioningId(null);
    }
  };

  const handleReject = async (id) => {
    const note = prompt('Rejection note (optional):') || '';
    setActioningId(id);
    try {
      await admin.rejectPayout(id, note);
      toast.success('Payout rejected');
      loadRequests();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reject payout');
    } finally {
      setActioningId(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Wallet className="w-8 h-8" /> Payout Requests
        </h1>
        <Button onClick={loadRequests} disabled={loading} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
        </div>
      ) : requests.length === 0 ? (
        <Card className="p-8 text-center">
          <Wallet className="w-12 h-12 mx-auto text-stone-300 mb-3" />
          <p className="text-stone-500">No payout requests found</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {requests.map((req) => (
            <Card key={req.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-semibold">Vendor #{(req.vendor_id || '').slice(0, 8)}</p>
                  <p className="text-sm text-stone-500">Requested: {new Date(req.requested_at || Date.now()).toLocaleString()}</p>
                  {req.payout_date && (
                    <p className="text-xs text-stone-500">Paid: {new Date(req.payout_date).toLocaleString()}</p>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-lg font-semibold">Rs {Number(req.amount || 0).toLocaleString()}</p>
                    <StatusBadge status={req.status} />
                  </div>
                  {req.status === 'pending' && (
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleApprove(req.id)} disabled={actioningId === req.id}>
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleReject(req.id)} disabled={actioningId === req.id}>
                        Reject
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminPayouts;
