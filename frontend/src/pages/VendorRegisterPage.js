import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Progress } from '../components/ui/progress';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import AssistantWidget from '../components/assistant/AssistantWidget';
import { vendorRegister, categories } from '../lib/api';
import { FALLBACK_CATEGORIES } from '../lib/fallbackCategories';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';

const STORAGE_KEY = 'shadiro-vendor-register-v2';
const PRODUCT_CATEGORY_IDS = ['cat-grocery'];
const CATEGORY_META = {
  'cat-grocery': { icon: '🛒', headline: 'Sell groceries with delivery-ready setup', tone: 'product' },
  'cat-entertainment': { icon: '🎧', headline: 'DJ / Entertainment', tone: 'service', special: 'dj' },
  'cat-catering': { icon: '🍽', headline: 'Catering & Bakery', tone: 'service', special: 'caterer' },
  'cat-photography': { icon: '📸', headline: 'Photo & Video', tone: 'service', special: 'photographer' },
  'cat-decor': { icon: '🎨', headline: 'Decor & Florist', tone: 'service', special: 'decorator' },
  'cat-venues': { icon: '🏛', headline: 'Venues', tone: 'service', special: 'venue' },
  'cat-makeup': { icon: '💄', headline: 'Makeup Artist', tone: 'service', special: 'makeup' },
  'cat-transport': { icon: '🚐', headline: 'Transport / Rentals', tone: 'service', special: 'transport' },
  'cat-mehandi': { icon: '🪔', headline: 'Mehandi', tone: 'service', special: 'mehandi' },
};
const GROCERY_ITEMS = ['Rice', 'Wheat', 'Pulses', 'Spices', 'Dry Fruits', 'Vegetables', 'Fruits', 'Beverages', 'Others'];
const DJ_EQUIPMENT = ['Sound console', 'Lighting rig', 'Wireless mics', 'Smoke machine', 'Backup power'];
const MENU_TYPES = ['Veg', 'Non-Veg', 'Jain', 'Vegan', 'Desserts', 'Live counters'];
const PHOTO_DELIVERABLES = ['Candid photos', 'Traditional photos', 'Trailer film', 'Full documentary', 'Albums'];
const DECOR_THEMES = ['Minimal floral', 'Royal gold', 'Boho chic', 'Pastel garden', 'Neon sangeet'];

const TagInput = ({ label, placeholder, values, onChange, helper }) => {
  const [value, setValue] = useState('');
  const addTag = () => {
    const next = (value || '').trim();
    if (!next) return;
    if (values.includes(next)) {
      setValue('');
      return;
    }
    onChange([...values, next]);
    setValue('');
  };

  return (
    <div className="space-y-2">
      {(label || helper) && (
        <div className="flex items-center justify-between">
          {label && <Label className="text-sm text-stone-700">{label}</Label>}
          {helper && <span className="text-xs text-stone-500">{helper}</span>}
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        {values.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs"
          >
            {tag}
            <button
              type="button"
              onClick={() => onChange(values.filter((t) => t !== tag))}
              className="text-[11px] text-primary/70 hover:text-primary"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addTag();
          }
        }}
        placeholder={placeholder}
        className="h-11 rounded-lg"
      />
      <div className="text-[11px] text-stone-500">Press Enter to add</div>
    </div>
  );
};

const StepShell = ({ eyebrow, title, subtitle, children, side }) => (
  <Card className="p-6 md:p-8 bg-white/80 backdrop-blur border border-white/70 shadow-lg shadow-primary/5">
    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
      <div className="space-y-1">
        {eyebrow && <p className="text-xs uppercase tracking-[0.2em] text-primary/80">{eyebrow}</p>}
        <h2 className="text-2xl font-semibold text-stone-900">{title}</h2>
        {subtitle && <p className="text-sm text-stone-600">{subtitle}</p>}
      </div>
      {side}
    </div>
    <div className="mt-6 space-y-6">{children}</div>
  </Card>
);

const ProgressBadge = ({ value }) => (
  <div className="relative w-16 h-16">
    <div
      className="absolute inset-0 rounded-full"
      style={{ background: `conic-gradient(#1f4b99 ${value * 3.6}deg, #e5e7eb 0deg)` }}
    />
    <div className="absolute inset-1 rounded-full bg-white flex items-center justify-center shadow-inner">
      <div className="text-center">
        <p className="text-xs text-stone-500">Progress</p>
        <p className="text-lg font-semibold text-stone-900">{value}%</p>
      </div>
    </div>
  </div>
);

const compact = (obj = {}) =>
  Object.fromEntries(
    Object.entries(obj).filter(([_, v]) => {
      if (v === null || v === undefined) return false;
      if (typeof v === 'string' && v.trim() === '') return false;
      if (Array.isArray(v) && v.length === 0) return false;
      return true;
    })
  );

const VendorRegisterPage = () => {
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();

  const [loading, setLoading] = useState(false);
  const [catList, setCatList] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [otpRequested, setOtpRequested] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);

  const [basic, setBasic] = useState({
    business_name: '',
    owner_name: '',
    email: '',
    phone: '',
    password: '',
    city: '',
    years_of_experience: '',
    description: '',
  });
  const [serviceAreas, setServiceAreas] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [categoryId, setCategoryId] = useState('');
  const [vendorType, setVendorType] = useState('service_vendor');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });

  const [servicesOffered, setServicesOffered] = useState([]);
  const [eventTypes, setEventTypes] = useState([]);
  const [advanceBookingRequired, setAdvanceBookingRequired] = useState(false);
  const [availabilityNote, setAvailabilityNote] = useState('');

  const [djEquipment, setDjEquipment] = useState([]);
  const [djCrewSize, setDjCrewSize] = useState('');
  const [djSetupTime, setDjSetupTime] = useState('');

  const [menuTypes, setMenuTypes] = useState([]);
  const [perPlateRange, setPerPlateRange] = useState({ min: '', max: '' });
  const [kitchenAvailable, setKitchenAvailable] = useState(true);

  const [photoDeliverables, setPhotoDeliverables] = useState([]);
  const [deliveryTimeline, setDeliveryTimeline] = useState('');

  const [decorThemes, setDecorThemes] = useState([]);
  const [decorInventory, setDecorInventory] = useState([]);

  const [groceryBasics, setGroceryBasics] = useState({
    store_type: 'retail',
    delivery_radius: 5,
    minimum_order_value: '',
    same_day_delivery: true,
  });
  const [groceryTags, setGroceryTags] = useState([]);
  const [groceryProducts, setGroceryProducts] = useState([{ name: '', unit: 'kg', unit_price: '' }]);

  const [errors, setErrors] = useState({});

  useEffect(() => {
    setCategoriesLoading(true);
    categories
      .getAll()
      .then((r) => {
        const data = r?.data;
        setCatList(Array.isArray(data) && data.length > 0 ? data : FALLBACK_CATEGORIES);
      })
      .catch(() => setCatList(FALLBACK_CATEGORIES))
      .finally(() => setCategoriesLoading(false));
  }, []);

  useEffect(() => {
    const draft = localStorage.getItem(STORAGE_KEY);
    if (!draft) return;
    try {
      const d = JSON.parse(draft);
      setBasic(d.basic || basic);
      setServiceAreas(d.serviceAreas || []);
      setHighlights(d.highlights || []);
      setCategoryId(d.categoryId || '');
      setVendorType(d.vendorType || 'service_vendor');
      setPriceRange(d.priceRange || { min: '', max: '' });
      setServicesOffered(d.servicesOffered || []);
      setEventTypes(d.eventTypes || []);
      setAdvanceBookingRequired(d.advanceBookingRequired || false);
      setAvailabilityNote(d.availabilityNote || '');
      setDjEquipment(d.djEquipment || []);
      setDjCrewSize(d.djCrewSize || '');
      setDjSetupTime(d.djSetupTime || '');
      setMenuTypes(d.menuTypes || []);
      setPerPlateRange(d.perPlateRange || { min: '', max: '' });
      setKitchenAvailable(d.kitchenAvailable ?? true);
      setPhotoDeliverables(d.photoDeliverables || []);
      setDeliveryTimeline(d.deliveryTimeline || '');
      setDecorThemes(d.decorThemes || []);
      setDecorInventory(d.decorInventory || []);
      setGroceryBasics(d.groceryBasics || groceryBasics);
      setGroceryTags(d.groceryTags || []);
      setGroceryProducts(d.groceryProducts || [{ name: '', unit: 'kg', unit_price: '' }]);
      setCurrentStep(d.currentStep || 0);
      setLastSaved(d.lastSaved || null);
    } catch {
      // ignore malformed drafts
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const payload = {
      basic,
      serviceAreas,
      highlights,
      categoryId,
      vendorType,
      priceRange,
      servicesOffered,
      eventTypes,
      advanceBookingRequired,
      availabilityNote,
      djEquipment,
      djCrewSize,
      djSetupTime,
      menuTypes,
      perPlateRange,
      kitchenAvailable,
      photoDeliverables,
      deliveryTimeline,
      decorThemes,
      decorInventory,
      groceryBasics,
      groceryTags,
      groceryProducts,
      currentStep,
      lastSaved: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    setLastSaved(payload.lastSaved);
  }, [
    basic,
    serviceAreas,
    highlights,
    categoryId,
    vendorType,
    priceRange,
    servicesOffered,
    eventTypes,
    advanceBookingRequired,
    availabilityNote,
    djEquipment,
    djCrewSize,
    djSetupTime,
    menuTypes,
    perPlateRange,
    kitchenAvailable,
    photoDeliverables,
    deliveryTimeline,
    decorThemes,
    decorInventory,
    groceryBasics,
    groceryTags,
    groceryProducts,
    currentStep,
  ]);

  const isProductFlow = useMemo(
    () => PRODUCT_CATEGORY_IDS.includes(categoryId) || CATEGORY_META[categoryId]?.tone === 'product',
    [categoryId]
  );

  const steps = useMemo(
    () => [
      { key: 'welcome', label: 'Welcome', percent: 5 },
      { key: 'basic', label: 'Basic Details', percent: 20 },
      { key: 'category', label: 'Choose Category', percent: 35 },
      { key: 'setup', label: isProductFlow ? 'Store Setup' : 'Service Setup', percent: isProductFlow ? 60 : 70 },
      { key: 'assist', label: 'Helpful AI', percent: 85 },
      { key: 'review', label: 'Review & Finish', percent: 100 },
    ],
    [isProductFlow]
  );

  useEffect(() => {
    if (currentStep > steps.length - 1) setCurrentStep(steps.length - 1);
  }, [steps.length, currentStep]);

  const progressValue = steps[currentStep]?.percent || 0;
  const selectedCategory = useMemo(() => catList.find((c) => c.id === categoryId), [catList, categoryId]);
  const categoryMeta = CATEGORY_META[categoryId] || {};

  const setBasicField = (key, value) => setBasic((prev) => ({ ...prev, [key]: value }));
  const normalizePhone = (value) => {
    const digits = (value || '').replace(/\D/g, '');
    if (digits.length === 12 && digits.startsWith('91')) return digits.slice(2);
    return digits;
  };

  const handleNext = () => {
    const key = steps[currentStep]?.key;
    const nextErrors = {};
    if (key === 'basic') {
      if (!basic.business_name) nextErrors.business_name = 'Business name is required';
      if (!basic.owner_name) nextErrors.owner_name = 'Owner name is required';
      if (!basic.email) nextErrors.email = 'Email is required';
      if (!basic.phone) nextErrors.phone = 'Phone is required';
      if (normalizePhone(basic.phone).length !== 10) nextErrors.phone = 'Phone must be exactly 10 digits';
      if (!basic.password || basic.password.length < 8) nextErrors.password = 'Password must be at least 8 characters';
      if (!basic.city) nextErrors.city = 'City is required';
    }
    if (key === 'category' && !categoryId) nextErrors.category_id = 'Select a category to continue';
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      toast.error('Complete the required fields to continue');
      return;
    }
    setCurrentStep((s) => Math.min(s + 1, steps.length - 1));
  };

  const handleBack = () => setCurrentStep((s) => Math.max(s - 1, 0));

  const handleSubmit = async () => {
    const required = ['business_name', 'owner_name', 'email', 'phone', 'password', 'city'];
    const missing = required.filter((f) => !basic[f]);
    if (!categoryId) missing.push('category_id');
    if (missing.length) {
      toast.error('Please fill required fields before finishing');
      setCurrentStep(1);
      return;
    }
    const normalizedPhone = normalizePhone(basic.phone);
    if (normalizedPhone.length !== 10) {
      toast.error('Phone must be exactly 10 digits');
      setCurrentStep(1);
      return;
    }
    if ((basic.password || '').length < 8) {
      toast.error('Password must be at least 8 characters');
      setCurrentStep(1);
      return;
    }

    const details = compact({
      vendor_type: vendorType,
      onboarding_stage: steps[currentStep]?.key,
      event_types_supported: eventTypes,
      advance_booking_required: advanceBookingRequired,
      availability_note: availabilityNote,
      dj_setup_time: djSetupTime,
      kitchen_available: kitchenAvailable,
      delivery_timeline: deliveryTimeline,
      same_day_delivery: groceryBasics.same_day_delivery,
      store_type: groceryBasics.store_type,
      minimum_order_value: groceryBasics.minimum_order_value ? Number(groceryBasics.minimum_order_value) : null,
      what_you_sell: groceryTags,
      decor_inventory: decorInventory,
    });

    const payload = compact({
      business_name: basic.business_name.trim(),
      owner_name: basic.owner_name.trim(),
      email: basic.email.trim(),
      phone: normalizedPhone,
      password: basic.password,
      category_id: categoryId,
      city: basic.city.trim(),
      service_areas: serviceAreas,
      years_of_experience: basic.years_of_experience ? parseInt(basic.years_of_experience, 10) : null,
      price_min: priceRange.min ? parseFloat(priceRange.min) : null,
      price_max: priceRange.max ? parseFloat(priceRange.max) : null,
      description: basic.description || null,
      highlights,
      services_offered: servicesOffered,
      // Keep strict model fields minimal to avoid nested-shape 422s.
      // Advanced setup remains available under flexible `details`.
      details: compact({
        ...details,
        delivery_radius: isProductFlow ? `${groceryBasics.delivery_radius} km` : null,
        dj_equipment: djEquipment,
        dj_crew_size: djCrewSize ? parseInt(djCrewSize, 10) : null,
        caterer_price_per_plate:
          perPlateRange.min || perPlateRange.max
            ? parseFloat((Number(perPlateRange.min || 0) + Number(perPlateRange.max || perPlateRange.min || 0)) / 2)
            : null,
        delivery_timeline: deliveryTimeline || null,
        decorator_themes: decorThemes,
        decorator_inventory: decorInventory,
        grocery_items: groceryProducts
          .filter((p) => p.name && p.unit_price)
          .map((p) => ({ name: p.name, unit: p.unit || 'unit', unit_price: Number(p.unit_price), availability: 'in_stock' })),
      }),
    });

    try {
      setLoading(true);
      const res = await vendorRegister.register(payload);
      const { access_token, user: userData } = res.data;
      loginWithToken(access_token, userData);
      toast.success('Vendor registration submitted! You can finish details anytime.');
      navigate('/vendor-dashboard');
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((d) => d?.msg || '').filter(Boolean).join(', ')
        : (typeof detail === 'string' ? detail : 'Registration failed');

      if (typeof message === 'string' && message.toLowerCase().includes('email already registered')) {
        toast.error('Email already registered. Please login with this email.');
        navigate('/auth', {
          state: {
            defaultTab: 'login',
            prefillEmail: basic.email?.trim() || '',
          },
        });
        return;
      }

      toast.error(message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const renderWelcome = () => (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-primary/80">Vendors · Premium Onboarding</p>
          <h1 className="text-4xl md:text-5xl font-bold text-stone-900 mt-2">Grow your business on Shadiro</h1>
          <p className="text-stone-600 mt-3 text-lg">Join trusted local vendors and get bookings from real customers.</p>
        </div>
        <ProgressBadge value={progressValue} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="p-6 bg-gradient-to-br from-primary/10 via-white to-amber-50 border-none shadow-xl">
          <p className="text-sm text-primary font-semibold">Why vendors choose us</p>
          <ul className="mt-3 space-y-2 text-stone-700">
            <li>• Smart leads matched by category & city</li>
            <li>• Fast payouts with transparent tracking</li>
            <li>• AI helper to finish onboarding quickly</li>
          </ul>
          <div className="flex items-center gap-2 mt-4">
            <Badge className="bg-white/80 text-primary border-primary/20">Secure</Badge>
            <Badge className="bg-white/80 text-primary border-primary/20">Verified</Badge>
            <Badge className="bg-white/80 text-primary border-primary/20">Fast payouts</Badge>
          </div>
        </Card>
        <Card className="p-6 bg-white border border-stone-100 shadow-lg">
          <p className="text-stone-700">
            Soft gradients, rounded cards, and large touch targets keep the experience calm and premium.
          </p>
          <div className="mt-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-2xl">✨</div>
            <div>
              <p className="text-sm text-stone-500">Built for mobile</p>
              <p className="font-semibold text-stone-900">One decision per screen</p>
            </div>
          </div>
        </Card>
      </div>
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="text-sm text-stone-600">Start now — you can edit everything later.</div>
        <Button
          onClick={handleNext}
          className="h-12 px-6 rounded-full bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/20"
        >
          Start Registration
        </Button>
      </div>
    </div>
  );

  const renderBasic = () => (
    <StepShell
      eyebrow="Step 2 · 20%"
      title="Basic details"
      subtitle="Minimal inputs, inline validation, and reassurance that you can edit later."
      side={<ProgressBadge value={progressValue} />}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <Label>Business Name *</Label>
          <Input
            autoFocus
            className="mt-2 h-11 rounded-lg"
            value={basic.business_name}
            onChange={(e) => setBasicField('business_name', e.target.value)}
            placeholder="Shadiro Decor Studio"
          />
          {errors.business_name && <p className="text-xs text-red-600 mt-1">{errors.business_name}</p>}
        </div>
        <div>
          <Label>Owner Name *</Label>
          <Input
            className="mt-2 h-11 rounded-lg"
            value={basic.owner_name}
            onChange={(e) => setBasicField('owner_name', e.target.value)}
            placeholder="Full name"
          />
          {errors.owner_name && <p className="text-xs text-red-600 mt-1">{errors.owner_name}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <Label>Email *</Label>
          <Input
            type="email"
            className="mt-2 h-11 rounded-lg"
            value={basic.email}
            onChange={(e) => setBasicField('email', e.target.value)}
            placeholder="business@email.com"
          />
          {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
        </div>
        <div>
          <div className="flex items-center justify-between">
            <Label>Phone *</Label>
            <span className="text-xs text-stone-500">OTP optional</span>
          </div>
          <div className="mt-2 flex gap-2">
            <Input
              className="h-11 rounded-lg flex-1"
              value={basic.phone}
              onChange={(e) => setBasicField('phone', e.target.value)}
              placeholder="10-digit phone number"
              maxLength={10}
              pattern="[0-9]{10}"
            />
            <Button
              type="button"
              variant="outline"
              className="rounded-full"
              onClick={() => {
                setOtpRequested(true);
                toast.success('We’ll verify this during onboarding. You can continue without OTP.');
              }}
            >
              {otpRequested ? 'OTP later' : 'Send OTP'}
            </Button>
          </div>
          {errors.phone && <p className="text-xs text-red-600 mt-1">{errors.phone}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <Label>Password *</Label>
          <Input
            type="password"
            className="mt-2 h-11 rounded-lg"
            value={basic.password}
            onChange={(e) => setBasicField('password', e.target.value)}
            placeholder="Min 8 characters"
            minLength={8}
          />
          {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password}</p>}
        </div>
        <div>
          <Label>City *</Label>
          <Input
            className="mt-2 h-11 rounded-lg"
            value={basic.city}
            onChange={(e) => setBasicField('city', e.target.value)}
            placeholder="Mumbai, Delhi..."
          />
          {errors.city && <p className="text-xs text-red-600 mt-1">{errors.city}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <Label>Years of Experience</Label>
          <Input
            type="number"
            min={0}
            className="mt-2 h-11 rounded-lg"
            value={basic.years_of_experience}
            onChange={(e) => setBasicField('years_of_experience', e.target.value)}
            placeholder="5"
          />
        </div>
        <div>
          <Label>Service Areas</Label>
          <TagInput
            values={serviceAreas}
            onChange={setServiceAreas}
            placeholder="Add a city or locality"
            helper="You can edit later"
            label=""
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea
          className="mt-1 min-h-[90px] rounded-xl"
          value={basic.description}
          onChange={(e) => setBasicField('description', e.target.value)}
          placeholder="Tell customers about your services..."
        />
      </div>

      <div className="space-y-2">
        <Label>Highlights (one per line)</Label>
        <Textarea
          className="min-h-[80px] rounded-xl"
          value={highlights.join('\n')}
          onChange={(e) => setHighlights(e.target.value.split('\n').filter(Boolean))}
          placeholder="Award-winning team&#10;500+ events&#10;Same-day response"
        />
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
        <div className="text-sm text-stone-500">
          Save & continue. Draft is auto-saved {lastSaved ? `(${new Date(lastSaved).toLocaleTimeString()})` : ''}.
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-full" onClick={handleBack}>
            Back
          </Button>
          <Button className="rounded-full px-6" onClick={handleNext}>
            Save & Continue
          </Button>
        </div>
      </div>
    </StepShell>
  );

  const renderCategory = () => (
    <StepShell
      eyebrow="Step 3 · 35%"
      title="Choose what you do"
      subtitle="We’ll show only what’s relevant. Tap a card to move ahead."
      side={<ProgressBadge value={progressValue} />}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(catList || []).map((cat) => {
          const meta = CATEGORY_META[cat.id] || {};
          const isActive = categoryId === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => {
                setCategoryId(cat.id);
                setVendorType(PRODUCT_CATEGORY_IDS.includes(cat.id) ? 'product_vendor' : 'service_vendor');
                setTimeout(() => setCurrentStep((s) => Math.min(s + 1, steps.length - 1)), 150);
              }}
              className={cn(
                'text-left rounded-2xl border transition transform hover:-translate-y-1 bg-white p-5 shadow-sm',
                isActive ? 'border-primary shadow-lg shadow-primary/15' : 'border-stone-100'
              )}
            >
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-2xl">
                  {meta.icon || '✨'}
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-stone-900">{cat.name}</p>
                  <p className="text-xs text-stone-600">{meta.headline || cat.description}</p>
                  <div className="flex gap-2">
                    <Badge className="bg-stone-50 text-stone-600 border-stone-200">
                      {categoriesLoading ? 'Loading…' : 'Relevant only'}
                    </Badge>
                    {PRODUCT_CATEGORY_IDS.includes(cat.id) && (
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-100">Product flow</Badge>
                    )}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
        <p className="text-sm text-stone-500">Selecting a card will move you to the next step.</p>
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-full" onClick={handleBack}>
            Back
          </Button>
          <Button className="rounded-full px-6" onClick={handleNext}>
            Continue
          </Button>
        </div>
      </div>
    </StepShell>
  );

  const renderGrocerySetup = () => (
    <StepShell
      eyebrow="Step 4 · 60%"
      title="Set up your store — customers will shop directly from you"
      subtitle="Smart defaults applied. You can add products later without blocking registration."
      side={<ProgressBadge value={progressValue} />}
    >
      <div className="grid gap-4">
        <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <p className="font-semibold text-stone-900">Store basics</p>
            <Badge className="bg-primary/10 text-primary border-primary/20">Required</Badge>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Store Type</Label>
              <Select
                value={groceryBasics.store_type}
                onValueChange={(v) => setGroceryBasics((prev) => ({ ...prev, store_type: v }))}
              >
                <SelectTrigger className="mt-2 h-11 rounded-lg">
                  <SelectValue placeholder="Retail or Wholesale" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="retail">Retail</SelectItem>
                  <SelectItem value="wholesale">Wholesale</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Delivery Radius: {groceryBasics.delivery_radius} km</Label>
              <div className="mt-3">
                <Slider
                  value={[groceryBasics.delivery_radius]}
                  onValueChange={([v]) => setGroceryBasics((prev) => ({ ...prev, delivery_radius: v }))}
                  max={25}
                  min={1}
                  step={1}
                />
              </div>
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <div>
              <Label>Minimum Order Value</Label>
              <Input
                type="number"
                className="mt-2 h-11 rounded-lg"
                value={groceryBasics.minimum_order_value}
                onChange={(e) => setGroceryBasics((prev) => ({ ...prev, minimum_order_value: e.target.value }))}
                placeholder="500"
              />
            </div>
            <div className="flex items-center justify-between bg-stone-50 rounded-lg px-4 py-3 mt-6 md:mt-8">
              <div>
                <p className="text-sm font-semibold text-stone-900">Same-day delivery</p>
                <p className="text-xs text-stone-600">Toggle off if you need prep time</p>
              </div>
              <Switch
                checked={groceryBasics.same_day_delivery}
                onCheckedChange={(v) => setGroceryBasics((prev) => ({ ...prev, same_day_delivery: v }))}
              />
            </div>
          </div>
        </Card>

        <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <p className="font-semibold text-stone-900">What you sell</p>
            <Badge className="bg-stone-50 text-stone-700 border-stone-200">Smart defaults</Badge>
          </div>
          <div className="flex flex-wrap gap-2">
            {GROCERY_ITEMS.map((item) => (
              <button
                type="button"
                key={item}
                onClick={() =>
                  setGroceryTags((tags) => (tags.includes(item) ? tags.filter((t) => t !== item) : [...tags, item]))
                }
                className={cn(
                  'px-3 py-2 rounded-full text-sm border transition',
                  groceryTags.includes(item)
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white border-stone-200 text-stone-700'
                )}
              >
                {item}
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-5 bg-white border border-dashed border-primary/30 rounded-xl shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="font-semibold text-stone-900">Add products (optional now)</p>
              <p className="text-sm text-stone-600">You can skip — progress still counts.</p>
            </div>
            <Badge className="bg-emerald-50 text-emerald-700 border-emerald-100">Optional</Badge>
          </div>
          <div className="space-y-3">
            {groceryProducts.map((row, idx) => (
              <div key={idx} className="grid md:grid-cols-3 gap-3">
                <Input
                  placeholder="Product name"
                  value={row.name}
                  onChange={(e) =>
                    setGroceryProducts((list) =>
                      list.map((item, i) => (i === idx ? { ...item, name: e.target.value } : item))
                    )
                  }
                  className="h-11 rounded-lg"
                />
                <Input
                  type="number"
                  placeholder="Unit price"
                  value={row.unit_price}
                  onChange={(e) =>
                    setGroceryProducts((list) =>
                      list.map((item, i) => (i === idx ? { ...item, unit_price: e.target.value } : item))
                    )
                  }
                  className="h-11 rounded-lg"
                />
                <div className="flex gap-2">
                  <Input
                    placeholder="Unit (kg, pcs)"
                    value={row.unit}
                    onChange={(e) =>
                      setGroceryProducts((list) =>
                        list.map((item, i) => (i === idx ? { ...item, unit: e.target.value } : item))
                      )
                    }
                    className="h-11 rounded-lg"
                  />
                  <Button
                    variant="ghost"
                    className="rounded-full px-3"
                    onClick={() => setGroceryProducts((list) => list.filter((_, i) => i !== idx || list.length === 1))}
                    type="button"
                  >
                    ✕
                  </Button>
                </div>
              </div>
            ))}
            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                className="rounded-full"
                onClick={() => setGroceryProducts([...groceryProducts, { name: '', unit: 'kg', unit_price: '' }])}
              >
                + Add product
              </Button>
              <Button type="button" variant="ghost" className="text-stone-600 rounded-full">
                Add later
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
        <p className="text-sm text-stone-500">Progress shows even if you skip optional product details.</p>
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-full" onClick={handleBack}>
            Back
          </Button>
          <Button className="rounded-full px-6" onClick={handleNext}>
            Continue
          </Button>
        </div>
      </div>
    </StepShell>
  );

  const renderServiceSetup = () => (
    <StepShell
      eyebrow="Step 4 · 70%"
      title="Tell customers how you help make their event special"
      subtitle="Only relevant fields are shown. Optional fields never block registration."
      side={<ProgressBadge value={progressValue} />}
    >
      <div className="grid gap-4">
        <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
          <div className="grid md:grid-cols-2 gap-4">
            <TagInput
              label="Services Offered"
              values={servicesOffered}
              onChange={setServicesOffered}
              placeholder="Photography, Stage decor..."
              helper="Inline validation & smart tags"
            />
            <div className="grid gap-2">
              <Label>Starting price range</Label>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  className="h-11 rounded-lg"
                  value={priceRange.min}
                  onChange={(e) => setPriceRange((p) => ({ ...p, min: e.target.value }))}
                />
                <Input
                  type="number"
                  placeholder="Max"
                  className="h-11 rounded-lg"
                  value={priceRange.max}
                  onChange={(e) => setPriceRange((p) => ({ ...p, max: e.target.value }))}
                />
              </div>
              <p className="text-xs text-stone-500">Customers see a realistic starting range</p>
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <TagInput
              label="Event types supported"
              values={eventTypes}
              onChange={setEventTypes}
              placeholder="Wedding, Corporate..."
              helper="Used for better matches"
            />
            <div className="flex items-center justify-between bg-stone-50 rounded-lg px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-stone-900">Advance booking required?</p>
                <p className="text-xs text-stone-600">Toggle on if you need lead time</p>
              </div>
              <Switch checked={advanceBookingRequired} onCheckedChange={(v) => setAdvanceBookingRequired(v)} />
            </div>
          </div>
          <div className="mt-4">
            <Label>Availability (add detailed calendar later)</Label>
            <Textarea
              className="mt-2 rounded-xl"
              value={availabilityNote}
              onChange={(e) => setAvailabilityNote(e.target.value)}
              placeholder="Usually available with 3 days notice. Weekends fill fast."
            />
          </div>
        </Card>

        {categoryMeta.special === 'dj' && (
          <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold text-stone-900">DJ setup</p>
              <Badge className="bg-primary/10 text-primary border-primary/20">Category smart</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {DJ_EQUIPMENT.map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() =>
                    setDjEquipment((list) => (list.includes(item) ? list.filter((i) => i !== item) : [...list, item]))
                  }
                  className={cn(
                    'px-3 py-2 rounded-full text-sm border transition',
                    djEquipment.includes(item)
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white border-stone-200 text-stone-700'
                  )}
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="grid md:grid-cols-2 gap-4 mt-4">
              <div>
                <Label>Team size</Label>
                <Input
                  type="number"
                  className="mt-2 h-11 rounded-lg"
                  value={djCrewSize}
                  onChange={(e) => setDjCrewSize(e.target.value)}
                  placeholder="3"
                />
              </div>
              <div>
                <Label>Setup time needed</Label>
                <Input
                  className="mt-2 h-11 rounded-lg"
                  value={djSetupTime}
                  onChange={(e) => setDjSetupTime(e.target.value)}
                  placeholder="e.g., 60 mins"
                />
              </div>
            </div>
          </Card>
        )}

        {categoryMeta.special === 'caterer' && (
          <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold text-stone-900">Catering specifics</p>
              <Badge className="bg-primary/10 text-primary border-primary/20">Category smart</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {MENU_TYPES.map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() =>
                    setMenuTypes((list) => (list.includes(item) ? list.filter((i) => i !== item) : [...list, item]))
                  }
                  className={cn(
                    'px-3 py-2 rounded-full text-sm border transition',
                    menuTypes.includes(item)
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white border-stone-200 text-stone-700'
                  )}
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="grid md:grid-cols-2 gap-4 mt-4">
              <div>
                <Label>Per plate min</Label>
                <Input
                  type="number"
                  className="mt-2 h-11 rounded-lg"
                  value={perPlateRange.min}
                  onChange={(e) => setPerPlateRange((p) => ({ ...p, min: e.target.value }))}
                  placeholder="500"
                />
              </div>
              <div>
                <Label>Per plate max</Label>
                <Input
                  type="number"
                  className="mt-2 h-11 rounded-lg"
                  value={perPlateRange.max}
                  onChange={(e) => setPerPlateRange((p) => ({ ...p, max: e.target.value }))}
                  placeholder="1800"
                />
              </div>
            </div>
            <div className="flex items-center justify-between bg-stone-50 rounded-lg px-4 py-3 mt-4">
              <div>
                <p className="text-sm font-semibold text-stone-900">Kitchen available?</p>
                <p className="text-xs text-stone-600">If no, we’ll prompt for cloud kitchen later</p>
              </div>
              <Switch checked={kitchenAvailable} onCheckedChange={(v) => setKitchenAvailable(v)} />
            </div>
          </Card>
        )}

        {categoryMeta.special === 'photographer' && (
          <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold text-stone-900">Photography deliverables</p>
              <Badge className="bg-primary/10 text-primary border-primary/20">Category smart</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {PHOTO_DELIVERABLES.map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() =>
                    setPhotoDeliverables((list) => (list.includes(item) ? list.filter((i) => i !== item) : [...list, item]))
                  }
                  className={cn(
                    'px-3 py-2 rounded-full text-sm border transition',
                    photoDeliverables.includes(item)
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white border-stone-200 text-stone-700'
                  )}
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="mt-4">
              <Label>Delivery timeline</Label>
              <Input
                className="mt-2 h-11 rounded-lg"
                value={deliveryTimeline}
                onChange={(e) => setDeliveryTimeline(e.target.value)}
                placeholder="e.g., 21 days after event"
              />
            </div>
          </Card>
        )}

        {categoryMeta.special === 'decorator' && (
          <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold text-stone-900">Decorator preferences</p>
              <Badge className="bg-primary/10 text-primary border-primary/20">Category smart</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {DECOR_THEMES.map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() =>
                    setDecorThemes((list) => (list.includes(item) ? list.filter((i) => i !== item) : [...list, item]))
                  }
                  className={cn(
                    'px-3 py-2 rounded-full text-sm border transition',
                    decorThemes.includes(item)
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white border-stone-200 text-stone-700'
                  )}
                >
                  {item}
                </button>
              ))}
            </div>
            <TagInput
              label="Inventory items"
              values={decorInventory}
              onChange={setDecorInventory}
              placeholder="Stage props, fairy lights..."
              helper="Helps us auto-suggest packages"
            />
          </Card>
        )}
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
        <p className="text-sm text-stone-500">Optional data never blocks you. Progress keeps moving.</p>
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-full" onClick={handleBack}>
            Back
          </Button>
          <Button className="rounded-full px-6" onClick={handleNext}>
            Continue
          </Button>
        </div>
      </div>
    </StepShell>
  );

  const renderAssist = () => {
    const missing = [];
    if (!basic.business_name) missing.push('Business name');
    if (!basic.owner_name) missing.push('Owner name');
    if (!basic.email) missing.push('Email');
    if (!basic.phone) missing.push('Phone');
    if (!categoryId) missing.push('Category');

    return (
      <StepShell
        eyebrow="Step 5 · 85%"
        title="Need help? I’ll guide you."
        subtitle="Friendly, simple, and human. I’ll point out what’s missing and suggest pricing."
        side={<ProgressBadge value={progressValue} />}
      >
        <Card className="p-6 bg-gradient-to-br from-white to-primary/5 border-none shadow-lg shadow-primary/10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-primary/80">Assistant</p>
              <h3 className="text-xl font-semibold text-stone-900 mt-1">Friendly guidance</h3>
              <p className="text-sm text-stone-600 mt-1">
                I can tell what’s missing, suggest pricing, and explain benefits of completion.
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-stone-700">
                {missing.length === 0 && (
                  <Badge className="bg-emerald-50 text-emerald-700 border-emerald-100">You’re nearly done</Badge>
                )}
                {missing.slice(0, 4).map((item) => (
                  <Badge key={item} className="bg-white text-stone-700 border-stone-200">
                    Missing · {item}
                  </Badge>
                ))}
              </div>
            </div>
            <Button onClick={() => setCurrentStep((s) => Math.min(s + 1, steps.length - 1))} className="rounded-full px-6 h-11">
              Skip to review
            </Button>
          </div>
        </Card>
        <div className="text-sm text-stone-600">The floating card on the right stays available while you fill details.</div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
          <div className="text-sm text-stone-500">You can always come back to this step.</div>
          <div className="flex gap-3">
            <Button variant="outline" className="rounded-full" onClick={handleBack}>
              Back
            </Button>
            <Button className="rounded-full px-6" onClick={handleNext}>
              Continue
            </Button>
          </div>
        </div>
      </StepShell>
    );
  };

  const renderReview = () => (
    <StepShell
      eyebrow="Step 6 · 100%"
      title="Review & finish"
      subtitle="Clean summary with what’s missing (if any). Optional data never blocks submission."
      side={<ProgressBadge value={progressValue} />}
    >
      <Card className="p-5 bg-white border border-stone-100 rounded-xl shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <p className="font-semibold text-stone-900">Summary</p>
          <Badge className="bg-emerald-50 text-emerald-700 border-emerald-100">Ready to submit</Badge>
        </div>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-stone-700">
          <div>
            <p className="font-semibold text-stone-900">Basic info</p>
            <ul className="mt-2 space-y-1">
              <li>Business: {basic.business_name || '—'}</li>
              <li>Owner: {basic.owner_name || '—'}</li>
              <li>Email: {basic.email || '—'}</li>
              <li>Phone: {basic.phone || '—'}</li>
              <li>City: {basic.city || '—'}</li>
              <li>Service areas: {serviceAreas.length ? serviceAreas.join(', ') : '—'}</li>
            </ul>
          </div>
          <div>
            <p className="font-semibold text-stone-900">Category setup</p>
            <ul className="mt-2 space-y-1">
              <li>Category: {selectedCategory?.name || '—'}</li>
              <li>Type: {isProductFlow ? 'Product flow' : 'Service flow'}</li>
              <li>Services: {servicesOffered.length ? servicesOffered.join(', ') : '—'}</li>
              {isProductFlow ? (
                <li>What you sell: {groceryTags.length ? groceryTags.join(', ') : '—'}</li>
              ) : (
                <li>Event types: {eventTypes.length ? eventTypes.join(', ') : '—'}</li>
              )}
              <li>
                Pricing: {priceRange.min || priceRange.max ? `${priceRange.min || '?'} – ${priceRange.max || '?'}` : '—'}
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-4 p-4 rounded-xl bg-stone-50 text-sm text-stone-700">
          <p className="font-semibold text-stone-900">What’s missing (optional)</p>
          <ul className="mt-2 list-disc list-inside space-y-1">
            {!basic.description && <li>Description</li>}
            {!highlights.length && <li>Highlights</li>}
            {!servicesOffered.length && !isProductFlow && <li>Services offered</li>}
            {isProductFlow && groceryProducts.filter((p) => p.name && p.unit_price).length === 0 && <li>Products (optional)</li>}
          </ul>
        </div>
      </Card>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
        <p className="text-sm text-stone-600">Registration never fails because of optional data. You can edit later.</p>
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-full" onClick={handleBack}>
            Back
          </Button>
          <Button
            className="rounded-full px-6 bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/20"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Submitting...' : 'Complete Registration'}
          </Button>
        </div>
      </div>
      <p className="text-xs text-stone-500">You’re live! Complete your profile to get more bookings.</p>
    </StepShell>
  );

  const renderStep = () => {
    const key = steps[currentStep]?.key;
    if (key === 'welcome') return renderWelcome();
    if (key === 'basic') return renderBasic();
    if (key === 'category') return renderCategory();
    if (key === 'setup') return isProductFlow ? renderGrocerySetup() : renderServiceSetup();
    if (key === 'assist') return renderAssist();
    return renderReview();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 via-white to-primary/5">
      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-primary/80">Shadiro Vendor Hub</p>
            <h1 className="text-3xl font-bold text-stone-900">Premium vendor registration</h1>
            <p className="text-stone-600 mt-1">Minimal steps, clear progress, and mobile-first layout.</p>
          </div>
          <div className="w-full md:w-64">
            <Progress value={progressValue} />
            <p className="text-xs text-stone-500 mt-1">Smart progress · auto-save drafts</p>
          </div>
        </div>
        {renderStep()}
      </div>
      <AssistantWidget
        role="vendor"
        title="Onboarding Assistant"
        context={{
          category_id: categoryId,
          vendor_type: vendorType,
          profile: {
            business_name: basic.business_name,
            owner_name: basic.owner_name,
            city: basic.city,
            service_areas: serviceAreas,
            years_of_experience: basic.years_of_experience ? parseInt(basic.years_of_experience, 10) : null,
            price_min: priceRange.min ? parseFloat(priceRange.min) : null,
            price_max: priceRange.max ? parseFloat(priceRange.max) : null,
            description: basic.description || null,
            highlights,
            services_offered: servicesOffered,
            event_types: eventTypes,
            advance_booking_required: advanceBookingRequired,
          },
        }}
      />
    </div>
  );
};

export default VendorRegisterPage;
