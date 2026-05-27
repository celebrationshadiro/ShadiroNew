import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { vendors as vendorsApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';

const PlanMyEvent = () => {
  const navigate = useNavigate();
  const [city, setCity] = useState('');
  const [budget, setBudget] = useState('');
  const [eventType, setEventType] = useState('');
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [shortlist, setShortlist] = useState([]);

  const handlePlan = async () => {
    if (!city || !budget || !eventType || !date) {
      toast.error('Please fill budget, city, event type, and date');
      return;
    }
    setLoading(true);
    try {
      const res = await vendorsApi.getAll({ city, search: eventType, limit: 6 });
      setShortlist(res.data?.slice(0, 6) || []);
    } catch (err) {
      toast.error('Could not build shortlist right now');
      setShortlist([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckout = () => {
    if (shortlist.length === 0) {
      toast.error('Build a shortlist first');
      return;
    }
    navigate('/checkout', {
      state: {
        conciergeMode: true,
        shortlistedVendors: shortlist.map((v) => v.id),
        eventType,
        city,
        date,
        budget,
      },
    });
  };

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-5xl mx-auto px-4 md:px-8 py-10">
        <h1 className="text-4xl font-bold mb-2">“Mere paas jagah hai, sab tum dekh lo”</h1>
        <p className="text-stone-600 mb-6">Tell us your basics, we auto-assemble a crew and one combined quote.</p>

        <Card className="p-6 bg-white border border-stone-100 rounded-2xl mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-stone-600">City</label>
              <Input className="mt-1" value={city} onChange={(e) => setCity(e.target.value)} placeholder="Mumbai" />
            </div>
            <div>
              <label className="text-sm text-stone-600">Budget (₹)</label>
              <Input className="mt-1" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="200000" />
            </div>
            <div>
              <label className="text-sm text-stone-600">Event Type</label>
              <Select value={eventType} onValueChange={setEventType}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select event type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="wedding">Wedding</SelectItem>
                  <SelectItem value="corporate">Corporate</SelectItem>
                  <SelectItem value="social">Social</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-stone-600">Event Date</label>
              <Input className="mt-1" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <Button onClick={handlePlan} disabled={loading} className="rounded-full">
              {loading ? 'Planning...' : 'Build Shortlist'}
            </Button>
            <Button variant="outline" onClick={handleCheckout} className="rounded-full">
              One Checkout
            </Button>
          </div>
        </Card>

        {shortlist.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Suggested vendors</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {shortlist.map((v) => (
                <Card key={v.id} className="p-4 flex items-center justify-between border border-stone-200">
                  <div>
                    <p className="font-semibold">{v.business_name}</p>
                    <p className="text-sm text-stone-500">{v.city}</p>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => navigate(`/vendors/${v.id}`)}>
                    View
                  </Button>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlanMyEvent;
