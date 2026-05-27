import React, { useCallback, useEffect, useState } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { admin } from '../../lib/api';
import { ClipboardList, RefreshCw, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const AdminPlatformAuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    action_type: '',
    entity_type: '',
    performed_by: '',
    entity_id: '',
    start_date: '',
    end_date: '',
  });

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
      );
      const res = await admin.getPlatformAuditLogs(params);
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
  }, [filters]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const safeLogs = Array.isArray(logs) ? logs : [];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <ClipboardList className="w-8 h-8" /> Platform Audit Logs
        </h1>
        <Button onClick={loadLogs} disabled={loading} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      <Card className="p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Input
            placeholder="Action type"
            value={filters.action_type}
            onChange={(e) => setFilters((f) => ({ ...f, action_type: e.target.value }))}
          />
          <Input
            placeholder="Entity type"
            value={filters.entity_type}
            onChange={(e) => setFilters((f) => ({ ...f, entity_type: e.target.value }))}
          />
          <Input
            placeholder="Performed by (admin/vendor/system)"
            value={filters.performed_by}
            onChange={(e) => setFilters((f) => ({ ...f, performed_by: e.target.value }))}
          />
          <Input
            placeholder="Entity ID"
            value={filters.entity_id}
            onChange={(e) => setFilters((f) => ({ ...f, entity_id: e.target.value }))}
          />
          <Input
            type="datetime-local"
            value={filters.start_date}
            onChange={(e) => setFilters((f) => ({ ...f, start_date: e.target.value }))}
          />
          <Input
            type="datetime-local"
            value={filters.end_date}
            onChange={(e) => setFilters((f) => ({ ...f, end_date: e.target.value }))}
          />
        </div>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-stone-400" />
        </div>
      ) : safeLogs.length === 0 ? (
        <Card className="p-8 text-center">
          <ClipboardList className="w-12 h-12 mx-auto text-stone-300 mb-3" />
          <p className="text-stone-500">No audit logs found</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {safeLogs.map((log) => (
            <Card key={log.id} className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className="bg-stone-100 text-stone-700">{log.action_type || log.action || 'unknown'}</Badge>
                    <Badge className="bg-stone-100 text-stone-700">{log.entity_type || log.target_type || 'entity'}</Badge>
                    <Badge className="bg-stone-100 text-stone-700">{log.performed_by || log.actor_role || 'system'}</Badge>
                  </div>
                  <p className="text-sm text-stone-600">Entity: {log.entity_id || log.target_id || '-'}</p>
                  <p className="text-xs text-stone-500">
                    {new Date(log.timestamp || log.created_at || Date.now()).toLocaleString()}
                  </p>
                </div>
                <div className="text-xs text-stone-500 max-w-xl">
                  <div className="mb-1">Old: {JSON.stringify(log.old_value || {})}</div>
                  <div>New: {JSON.stringify(log.new_value || log.metadata || {})}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminPlatformAuditLogs;
