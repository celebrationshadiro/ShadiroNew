import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { admin } from '../../lib/api';
import { Activity, Loader2, FileText } from 'lucide-react';
import { toast } from 'sonner';

const actionTypeColors = {
  vendor_approve: 'bg-green-100 text-green-800',
  vendor_reject: 'bg-red-100 text-red-800',
  vendor_suspend: 'bg-orange-100 text-orange-800',
  vendor_featured: 'bg-yellow-100 text-yellow-800',
  user_blocked: 'bg-red-100 text-red-800',
  user_activated: 'bg-green-100 text-green-800',
  payment_refund: 'bg-purple-100 text-purple-800',
  dispute_resolved: 'bg-blue-100 text-blue-800',
};

const AdminAuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(50);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await admin.getAuditLogs({ skip, limit });
      const raw = res?.data;
      const list = Array.isArray(raw)
        ? raw
        : Array.isArray(raw?.items)
          ? raw.items
          : [];
      setLogs(list);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [skip, limit]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="w-8 h-8" /> Audit Logs
        </h1>
        <span className="text-sm text-stone-500">Total: {logs.length} actions</span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
        </div>
      ) : logs.length === 0 ? (
        <Card className="p-8 text-center">
          <FileText className="w-12 h-12 mx-auto text-stone-300 mb-3" />
          <p className="text-stone-500">No audit logs yet</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => (
            <Card key={log.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex flex-col space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <Badge className={actionTypeColors[log.action_type] || 'bg-stone-100'}>
                        {String(log.action_type || 'unknown').replace(/_/g, ' ').toUpperCase()}
                      </Badge>
                      <span className="text-sm text-stone-600 font-medium">
                        {log.target_type || 'target'}: {String(log.target_id || '').slice(0, 8)}
                      </span>
                      {!log.success && (
                        <Badge className="bg-red-100 text-red-800">Failed</Badge>
                      )}
                    </div>
                    
                    <div className="text-sm text-stone-600">
                      <p>Admin: <span className="font-mono text-xs">{String(log.admin_id || '').slice(0, 8)}</span></p>
                      {log.reason && (
                        <p>Reason: <span className="text-stone-800">{log.reason}</span></p>
                      )}
                      {log.ip_address && (
                        <p>IP: <span className="font-mono text-xs">{log.ip_address}</span></p>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="text-sm text-stone-500">
                      {formatDate(log.created_at)}
                    </p>
                  </div>
                </div>

                {(log.details || log.metadata) && Object.keys(log.details || log.metadata || {}).length > 0 && (
                  <div className="bg-stone-50 p-2 rounded text-xs text-stone-600">
                    <p className="font-mono">
                      Details: {JSON.stringify(log.details || log.metadata, null, 2)}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && logs.length > 0 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button
            onClick={() => setSkip(Math.max(0, skip - limit))}
            disabled={skip === 0}
            className="px-4 py-2 border border-stone-200 rounded-lg hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-sm text-stone-600">
            Showing {skip + 1} - {skip + logs.length}
          </span>
          <button
            onClick={() => setSkip(skip + limit)}
            disabled={logs.length < limit}
            className="px-4 py-2 border border-stone-200 rounded-lg hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default AdminAuditLogs;
