import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { automationApi } from '../../lib/api';
import { toast } from '../../components/ui/sonner';

const typeOptions = [
  { value: 'quote_followup', label: 'Quote Follow-up' },
  { value: 'booking_followup', label: 'Booking Follow-up' },
  { value: 'sla_alert', label: 'SLA Alert' },
  { value: 'event_reminder', label: 'Event Reminder' },
];

const AdminAutomation = () => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scheduleType, setScheduleType] = useState('quote_followup');
  const [runAt, setRunAt] = useState('');
  const [message, setMessage] = useState('');
  const [targetUser, setTargetUser] = useState('');
  const [targetVendor, setTargetVendor] = useState('');
  const [saving, setSaving] = useState(false);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const res = await automationApi.getQueue();
      setQueue(res.data.items || []);
    } catch (err) {
      toast.error('Failed to load automation queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleCreate = async () => {
    if (!runAt) {
      toast.error('Please set run time');
      return;
    }
    setSaving(true);
    try {
      await automationApi.createSchedule({
        type: scheduleType,
        run_at: new Date(runAt).toISOString(),
        payload: {
          message: message || undefined,
          user_id: targetUser || undefined,
          vendor_id: targetVendor || undefined,
          channel: 'email',
        },
      });
      setMessage('');
      setTargetUser('');
      setTargetVendor('');
      setRunAt('');
      toast.success('Automation scheduled');
      loadQueue();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to schedule automation');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Automation Console</h1>

      <Card className="p-6 bg-white rounded-2xl border border-stone-100 mb-8">
        <h2 className="text-lg font-semibold mb-4">Create Schedule</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-stone-500">Type</label>
            <Select value={scheduleType} onValueChange={setScheduleType}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {typeOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm text-stone-500">Run At</label>
            <Input type="datetime-local" value={runAt} onChange={(e) => setRunAt(e.target.value)} className="mt-1" />
          </div>
          <div>
            <label className="text-sm text-stone-500">User ID (optional)</label>
            <Input value={targetUser} onChange={(e) => setTargetUser(e.target.value)} className="mt-1" />
          </div>
          <div>
            <label className="text-sm text-stone-500">Vendor ID (optional)</label>
            <Input value={targetVendor} onChange={(e) => setTargetVendor(e.target.value)} className="mt-1" />
          </div>
          <div className="md:col-span-2">
            <label className="text-sm text-stone-500">Message</label>
            <Input value={message} onChange={(e) => setMessage(e.target.value)} className="mt-1" placeholder="Reminder message" />
          </div>
        </div>
        <div className="flex justify-end mt-6">
          <Button onClick={handleCreate} disabled={saving}>{saving ? 'Scheduling...' : 'Schedule'}</Button>
        </div>
      </Card>

      <Card className="p-6 bg-white rounded-2xl border border-stone-100">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Automation Queue</h2>
          <Button variant="outline" onClick={loadQueue}>Refresh</Button>
        </div>
        {loading ? (
          <p className="text-stone-500">Loading queue...</p>
        ) : queue.length === 0 ? (
          <p className="text-stone-500">No scheduled automations.</p>
        ) : (
          <div className="space-y-3">
            {queue.map((item) => (
              <div key={item.id} className="flex flex-col md:flex-row md:items-center md:justify-between border border-stone-100 rounded-xl p-4">
                <div>
                  <p className="font-medium">{item.type}</p>
                  <p className="text-sm text-stone-500">Run at: {item.run_at}</p>
                  {item.payload?.message && <p className="text-sm text-stone-500">{item.payload.message}</p>}
                </div>
                <span className={`mt-2 md:mt-0 px-3 py-1 rounded-full text-xs font-semibold ${item.status === 'pending' ? 'bg-amber-100 text-amber-700' : item.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-stone-100 text-stone-600'}`}>
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default AdminAutomation;
