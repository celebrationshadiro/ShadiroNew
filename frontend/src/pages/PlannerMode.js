import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { ChevronRight, Package, TrendingUp, MapPin, Users, Calendar, DollarSign, Star, Loader } from 'lucide-react';
import { toast } from 'sonner';
import '../styles/PlannerMode.css';

const PlannerMode = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [vendorBundles, setVendorBundles] = useState([]);

  // Form State
  const [plannerData, setPlannerData] = useState({
    eventType: 'wedding',
    eventDate: '',
    guestCount: '',
    city: '',
    budget: '',
    location: '',
    specialRequirements: '',
  });

  const eventTypes = [
    { value: 'wedding', label: '💍 Wedding', desc: 'Comprehensive wedding services' },
    { value: 'corporate', label: '🏢 Corporate Event', desc: 'Professional event planning' },
    { value: 'birthday', label: '🎉 Birthday Party', desc: 'Birthday celebration' },
    { value: 'engagement', label: '💐 Engagement', desc: 'Engagement ceremony' },
    { value: 'anniversary', label: '🎂 Anniversary', desc: 'Anniversary celebration' },
  ];

  const vendorCategories = {
    wedding: ['Event Venues', 'Wedding Planners', 'Caterers', 'Photographers', 'Decorators', 'DJs'],
    corporate: ['Event Venues', 'Caterers', 'Photographers', 'DJs', 'Decorators'],
    birthday: ['Event Venues', 'Caterers', 'Decorators', 'DJs', 'Photographers'],
    engagement: ['Event Venues', 'Caterers', 'Decorators', 'Photographers', 'Makeup Artists'],
    anniversary: ['Event Venues', 'Caterers', 'Decorators', 'Photographers', 'DJs'],
  };

  const handleInputChange = (field, value) => {
    setPlannerData({ ...plannerData, [field]: value });
  };

  const validateStep1 = () => {
    if (!plannerData.eventType) {
      toast.error('Please select event type');
      return false;
    }
    if (!plannerData.eventDate) {
      toast.error('Please select event date');
      return false;
    }
    if (!plannerData.guestCount || parseInt(plannerData.guestCount) <= 0) {
      toast.error('Please enter valid guest count');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!plannerData.city) {
      toast.error('Please select city');
      return false;
    }
    if (!plannerData.budget || parseFloat(plannerData.budget) <= 0) {
      toast.error('Please enter valid budget');
      return false;
    }
    return true;
  };

  const handleGeneratePlans = async () => {
    setLoading(true);
    try {
      // Simulate API call to generate vendor bundles
      // In production, this would call backend /api/planner/generate-bundles
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Mock vendor bundles based on budget
      const budgetNum = parseFloat(plannerData.budget);
      const bundles = generateBudgetBasedBundles(budgetNum);
      setVendorBundles(bundles);
      setStep(3);
    } catch (error) {
      console.error('Failed to generate plans:', error);
      toast.error('Failed to generate plans');
    } finally {
      setLoading(false);
    }
  };

  const generateBudgetBasedBundles = (budget) => {
    // Generate bundles based on percentages of budget
    const categories = vendorCategories[plannerData.eventType] || [];

    const bundles = [
      {
        id: 1,
        name: 'Essential Package',
        description: 'Core vendors for your event',
        estimatedCost: budget,
        allocations: {
          'Event Venues': (budget * 0.35).toLocaleString('en-IN'),
          'Caterers': (budget * 0.30).toLocaleString('en-IN'),
          'Decorators': (budget * 0.20).toLocaleString('en-IN'),
          'DJs': (budget * 0.15).toLocaleString('en-IN'),
        },
        vendors: 4,
        rating: 4.5,
      },
      {
        id: 2,
        name: 'Premium Package',
        description: 'Enhanced services with premium vendors',
        estimatedCost: budget * 1.3,
        allocations: {
          'Event Venues': ((budget * 1.3) * 0.35).toLocaleString('en-IN'),
          'Caterers': ((budget * 1.3) * 0.25).toLocaleString('en-IN'),
          'Photographers': ((budget * 1.3) * 0.15).toLocaleString('en-IN'),
          'Decorators': ((budget * 1.3) * 0.15).toLocaleString('en-IN'),
          'DJs': ((budget * 1.3) * 0.10).toLocaleString('en-IN'),
        },
        vendors: 5,
        rating: 4.8,
      },
      {
        id: 3,
        name: 'Luxury Package',
        description: 'Full-service planning with premium everything',
        estimatedCost: budget * 1.8,
        allocations: {
          'Event Venues': ((budget * 1.8) * 0.30).toLocaleString('en-IN'),
          'Wedding Planners': ((budget * 1.8) * 0.10).toLocaleString('en-IN'),
          'Caterers': ((budget * 1.8) * 0.25).toLocaleString('en-IN'),
          'Photographers': ((budget * 1.8) * 0.15).toLocaleString('en-IN'),
          'Decorators': ((budget * 1.8) * 0.12).toLocaleString('en-IN'),
          'DJs': ((budget * 1.8) * 0.08).toLocaleString('en-IN'),
        },
        vendors: 6,
        rating: 4.9,
      },
    ];

    return bundles;
  };

  const handleSelectBundle = (bundle) => {
    // In production, this would navigate to a checkout with pre-selected vendors
    localStorage.setItem('selectedBundle', JSON.stringify({
      ...bundle,
      ...plannerData,
    }));
    toast.success(`${bundle.name} selected! Proceeding to vendor selection...`);
    setTimeout(() => {
      navigate('/vendors');
    }, 1500);
  };

  // Step 1: Event Details
  if (step === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-stone-50 to-white py-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Package className="text-primary" size={32} />
              <h1 className="text-4xl md:text-5xl font-bold text-stone-900">Event Planner</h1>
            </div>
            <p className="text-lg text-stone-600 max-w-2xl mx-auto">
              Tell us about your event, and we'll automatically bundle the perfect vendors within your budget
            </p>
          </div>

          {/* Progress */}
          <div className="flex items-center justify-center gap-2 mb-12">
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">1</div>
            <div className="w-20 h-1 bg-stone-300"></div>
            <div className="w-10 h-10 rounded-full bg-stone-200 text-stone-600 flex items-center justify-center font-bold">2</div>
            <div className="w-20 h-1 bg-stone-300"></div>
            <div className="w-10 h-10 rounded-full bg-stone-200 text-stone-600 flex items-center justify-center font-bold">3</div>
          </div>

          <Card className="bg-white border-stone-200 p-8 md:p-12 shadow-lg rounded-2xl">
            <h2 className="text-2xl font-bold text-stone-900 mb-8">Step 1: Tell us about your event</h2>

            {/* Event Type Selection */}
            <div className="mb-10">
              <label className="block text-sm font-semibold text-stone-900 mb-4">What type of event?</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {eventTypes.map((type) => (
                  <button
                    key={type.value}
                    onClick={() => handleInputChange('eventType', type.value)}
                    className={`p-4 rounded-xl text-left transition-all ${
                      plannerData.eventType === type.value
                        ? 'bg-primary text-white border-2 border-primary'
                        : 'bg-stone-50 border-2 border-stone-200 hover:border-primary'
                    }`}
                  >
                    <p className="font-semibold mb-1">{type.label}</p>
                    <p className={`text-sm ${plannerData.eventType === type.value ? 'text-white/80' : 'text-stone-600'}`}>
                      {type.desc}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Date Input */}
            <div className="mb-8">
              <label className="block text-sm font-semibold text-stone-900 mb-2">Event Date</label>
              <div className="flex items-center gap-2">
                <Calendar className="text-stone-400" size={20} />
                <input
                  type="date"
                  value={plannerData.eventDate}
                  onChange={(e) => handleInputChange('eventDate', e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="flex-1 px-4 py-3 border border-stone-300 rounded-lg focus:border-primary focus:outline-none"
                />
              </div>
            </div>

            {/* Guest Count */}
            <div className="mb-8">
              <label className="block text-sm font-semibold text-stone-900 mb-2">Expected Guest Count</label>
              <div className="flex items-center gap-2">
                <Users className="text-stone-400" size={20} />
                <input
                  type="number"
                  min="1"
                  placeholder="e.g., 150"
                  value={plannerData.guestCount}
                  onChange={(e) => handleInputChange('guestCount', e.target.value)}
                  className="flex-1 px-4 py-3 border border-stone-300 rounded-lg focus:border-primary focus:outline-none"
                />
              </div>
            </div>

            {/* Special Requirements */}
            <div className="mb-12">
              <label className="block text-sm font-semibold text-stone-900 mb-2">Any Special Requirements? (Optional)</label>
              <textarea
                placeholder="e.g., vegetarian menu, outdoor setup, specific theme..."
                value={plannerData.specialRequirements}
                onChange={(e) => handleInputChange('specialRequirements', e.target.value)}
                rows="3"
                className="w-full px-4 py-3 border border-stone-300 rounded-lg focus:border-primary focus:outline-none"
              />
            </div>

            {/* Next Button */}
            <Button
              onClick={() => {
                if (validateStep1()) setStep(2);
              }}
              className="w-full h-14 bg-primary hover:bg-primary/90 text-white text-lg font-semibold rounded-full flex items-center justify-center"
            >
              Continue <ChevronRight className="ml-2" size={20} />
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  // Step 2: Budget & Location
  if (step === 2) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-stone-50 to-white py-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-stone-900 mb-2">Nearly there!</h1>
            <p className="text-stone-600">Help us understand your budget and location preferences</p>
          </div>

          {/* Progress */}
          <div className="flex items-center justify-center gap-2 mb-12">
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">1</div>
            <div className="w-20 h-1 bg-primary"></div>
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">2</div>
            <div className="w-20 h-1 bg-stone-300"></div>
            <div className="w-10 h-10 rounded-full bg-stone-200 text-stone-600 flex items-center justify-center font-bold">3</div>
          </div>

          <Card className="bg-white border-stone-200 p-8 md:p-12 shadow-lg rounded-2xl">
            <h2 className="text-2xl font-bold text-stone-900 mb-8">Step 2: Budget & Location</h2>

            {/* Summary */}
            <div className="grid grid-cols-3 gap-4 mb-10 p-6 bg-stone-50 rounded-xl">
              <div>
                <p className="text-xs text-stone-600 mb-1 uppercase font-semibold">Event</p>
                <p className="font-semibold text-stone-900 capitalize">
                  {eventTypes.find(t => t.value === plannerData.eventType)?.label}
                </p>
              </div>
              <div>
                <p className="text-xs text-stone-600 mb-1 uppercase font-semibold">Date</p>
                <p className="font-semibold text-stone-900">{new Date(plannerData.eventDate).toLocaleDateString('en-IN')}</p>
              </div>
              <div>
                <p className="text-xs text-stone-600 mb-1 uppercase font-semibold">Guests</p>
                <p className="font-semibold text-stone-900">{plannerData.guestCount}</p>
              </div>
            </div>

            {/* Budget Input */}
            <div className="mb-8">
              <label className="block text-sm font-semibold text-stone-900 mb-2">Total Budget (₹)</label>
              <div className="flex items-center gap-2">
                <DollarSign className="text-stone-400" size={20} />
                <input
                  type="number"
                  min="10000"
                  step="10000"
                  placeholder="e.g., 500000"
                  value={plannerData.budget}
                  onChange={(e) => handleInputChange('budget', e.target.value)}
                  className="flex-1 px-4 py-3 border border-stone-300 rounded-lg focus:border-primary focus:outline-none text-lg"
                />
              </div>
              <p className="text-xs text-stone-500 mt-2">We'll bundle vendors to match this budget</p>
            </div>

            {/* City Selection */}
            <div className="mb-8">
              <label className="block text-sm font-semibold text-stone-900 mb-2">City / Location</label>
              <div className="flex items-center gap-2">
                <MapPin className="text-stone-400" size={20} />
                <select
                  value={plannerData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  className="flex-1 px-4 py-3 border border-stone-300 rounded-lg focus:border-primary focus:outline-none"
                >
                  <option value="">Select city</option>
                  <option value="Mumbai">Mumbai</option>
                  <option value="Delhi">Delhi</option>
                  <option value="Bangalore">Bangalore</option>
                  <option value="Hyderabad">Hyderabad</option>
                  <option value="Pune">Pune</option>
                  <option value="Chennai">Chennai</option>
                  <option value="Ahmedabad">Ahmedabad</option>
                  <option value="Kolkata">Kolkata</option>
                </select>
              </div>
            </div>

            {/* Exact Location */}
            <div className="mb-12">
              <label className="block text-sm font-semibold text-stone-900 mb-2">Specific Location (Optional)</label>
              <input
                type="text"
                placeholder="e.g., Taj Lands End, Bandra"
                value={plannerData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                className="w-full px-4 py-3 border border-stone-300 rounded-lg focus:border-primary focus:outline-none"
              />
            </div>

            {/* Navigation */}
            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => setStep(1)}
                className="flex-1 h-14 border-stone-300 text-stone-700 text-lg font-semibold rounded-full"
              >
                Back
              </Button>
              <Button
                onClick={() => {
                  if (validateStep2()) handleGeneratePlans();
                }}
                disabled={loading}
                className="flex-1 h-14 bg-primary hover:bg-primary/90 text-white text-lg font-semibold rounded-full flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <Loader className="mr-2 animate-spin" size={20} />
                    Generating Plans...
                  </>
                ) : (
                  <>
                    Generate Plans <ChevronRight className="ml-2" size={20} />
                  </>
                )}
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  // Step 3: Vendor Bundles
  if (step === 3) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-stone-50 to-white py-12 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-stone-900 mb-4">Perfect Vendor Bundles</h1>
            <p className="text-lg text-stone-600">We've created 3 packages that fit your budget and event needs</p>
          </div>

          {/* Progress */}
          <div className="flex items-center justify-center gap-2 mb-12">
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">1</div>
            <div className="w-20 h-1 bg-primary"></div>
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">2</div>
            <div className="w-20 h-1 bg-primary"></div>
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold">3</div>
          </div>

          {/* Bundle Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {vendorBundles.map((bundle, idx) => (
              <Card
                key={bundle.id}
                className={`relative border-2 rounded-2xl overflow-hidden transition-all hover:shadow-2xl ${
                  idx === 1 ? 'border-primary md:scale-105' : 'border-stone-200 hover:border-primary/50'
                }`}
              >
                {idx === 1 && (
                  <div className="absolute top-4 right-4 bg-primary text-white px-3 py-1 rounded-full text-xs font-bold">
                    POPULAR
                  </div>
                )}

                <div className={`p-8 ${idx === 1 ? 'bg-gradient-to-br from-primary/10 to-primary/5' : 'bg-white'}`}>
                  {/* Title */}
                  <h3 className="text-2xl font-bold text-stone-900 mb-2">{bundle.name}</h3>
                  <p className="text-stone-600 mb-6 h-10">{bundle.description}</p>

                  {/* Price */}
                  <div className="mb-8 pb-8 border-b border-stone-200">
                    <p className="text-sm text-stone-600 mb-1">Estimated Total</p>
                    <p className="text-4xl font-bold text-primary">₹{Math.round(bundle.estimatedCost).toLocaleString('en-IN')}</p>
                  </div>

                  {/* Allocations */}
                  <div className="space-y-3 mb-8">
                    {Object.entries(bundle.allocations).map(([category, amount]) => (
                      <div key={category}>
                        <div className="flex justify-between items-center text-sm mb-1">
                          <span className="font-medium text-stone-700">{category}</span>
                          <span className="text-stone-600">₹{amount}</span>
                        </div>
                        <div className="w-full bg-stone-200 rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full"
                            style={{
                              width: `${(parseFloat(amount.replace(/,/g, '')) / Math.round(bundle.estimatedCost)) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 mb-8 p-4 bg-stone-50 rounded-lg">
                    <div>
                      <p className="text-xs text-stone-600">Vendors</p>
                      <p className="text-lg font-bold text-stone-900">{bundle.vendors}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Star className="text-amber-400 fill-amber-400" size={16} />
                      <div>
                        <p className="text-xs text-stone-600">Avg Rating</p>
                        <p className="text-lg font-bold text-stone-900">{bundle.rating}</p>
                      </div>
                    </div>
                  </div>

                  {/* Button */}
                  <Button
                    onClick={() => handleSelectBundle(bundle)}
                    className={`w-full h-12 rounded-full font-semibold ${
                      idx === 1
                        ? 'bg-primary hover:bg-primary/90 text-white'
                        : 'bg-stone-100 text-stone-900 hover:bg-stone-200'
                    }`}
                  >
                    Select Package
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {/* Info */}
          <div className="text-center">
            <Button
              variant="ghost"
              onClick={() => setStep(1)}
              className="text-stone-600 hover:text-primary"
            >
              Start Over
            </Button>
          </div>
        </div>
      </div>
    );
  }
};

export default PlannerMode;
