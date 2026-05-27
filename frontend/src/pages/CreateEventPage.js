import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { events as eventsApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

const CreateEventPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    event_type: 'wedding',
    date: '',
    location: '',
    guest_count: '',
    budget_min: '',
    budget_max: '',
    description: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      toast.error('Please login to create an event');
      navigate('/auth');
      return;
    }

    setLoading(true);
    try {
      const eventData = {
        ...formData,
        guest_count: formData.guest_count ? parseInt(formData.guest_count) : null,
        budget_min: formData.budget_min ? parseFloat(formData.budget_min) : null,
        budget_max: formData.budget_max ? parseFloat(formData.budget_max) : null,
      };
      
      await eventsApi.create(eventData);
      toast.success('Event created successfully!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to create event:', error);
      toast.error(error.response?.data?.detail || 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6"
          data-testid="back-button"
        >
          <ArrowLeft size={18} className="mr-2" /> Back
        </Button>

        <Card className="p-8 bg-white rounded-2xl shadow-lg">
          <h1 className="text-4xl font-semibold tracking-tight mb-2 font-heading">
            Create New Event
          </h1>
          <p className="text-stone-600 mb-8">Tell us about your event and we'll help you find the perfect vendors</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="title">Event Title *</Label>
              <Input
                id="title"
                placeholder="e.g., Sarah & John's Wedding"
                className="h-12 rounded-lg mt-2"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                required
                data-testid="event-title-input"
              />
            </div>

            <div>
              <Label htmlFor="event_type">Event Type *</Label>
              <Select value={formData.event_type} onValueChange={(value) => handleChange('event_type', value)}>
                <SelectTrigger className="h-12 rounded-lg mt-2" data-testid="event-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="wedding">Wedding</SelectItem>
                  <SelectItem value="corporate">Corporate Event</SelectItem>
                  <SelectItem value="birthday">Birthday Party</SelectItem>
                  <SelectItem value="anniversary">Anniversary</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="date">Event Date *</Label>
                <Input
                  id="date"
                  type="date"
                  className="h-12 rounded-lg mt-2"
                  value={formData.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                  required
                  data-testid="event-date-input"
                />
              </div>

              <div>
                <Label htmlFor="guest_count">Expected Guests</Label>
                <Input
                  id="guest_count"
                  type="number"
                  placeholder="e.g., 150"
                  className="h-12 rounded-lg mt-2"
                  value={formData.guest_count}
                  onChange={(e) => handleChange('guest_count', e.target.value)}
                  data-testid="guest-count-input"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="City or Venue Name"
                className="h-12 rounded-lg mt-2"
                value={formData.location}
                onChange={(e) => handleChange('location', e.target.value)}
                data-testid="location-input"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="budget_min">Min Budget (₹)</Label>
                <Input
                  id="budget_min"
                  type="number"
                  placeholder="e.g., 100000"
                  className="h-12 rounded-lg mt-2"
                  value={formData.budget_min}
                  onChange={(e) => handleChange('budget_min', e.target.value)}
                  data-testid="budget-min-input"
                />
              </div>

              <div>
                <Label htmlFor="budget_max">Max Budget (₹)</Label>
                <Input
                  id="budget_max"
                  type="number"
                  placeholder="e.g., 500000"
                  className="h-12 rounded-lg mt-2"
                  value={formData.budget_max}
                  onChange={(e) => handleChange('budget_max', e.target.value)}
                  data-testid="budget-max-input"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="description">Event Description</Label>
              <Textarea
                id="description"
                placeholder="Tell us more about your event..."
                className="rounded-lg mt-2 min-h-32"
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                data-testid="description-input"
              />
            </div>

            <div className="flex gap-4">
              <Button
                type="submit"
                className="flex-1 bg-primary hover:bg-primary/90 h-12 rounded-full text-base font-medium"
                disabled={loading}
                data-testid="create-event-submit"
              >
                {loading ? 'Creating...' : 'Create Event'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(-1)}
                className="px-8 h-12 rounded-full"
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default CreateEventPage;
