import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { useAuth } from '../contexts/AuthContext';
import { vendorProfile, assistantApi, vendors as vendorsApi } from '../lib/api';
import { toast } from 'sonner';

const CATEGORY_SLUG_MAP = {
  'cat-grocery': 'grocery',
  'cat-entertainment': 'entertainment',
  'cat-catering': 'catering',
  'cat-decor': 'decor',
  'cat-venues': 'venues',
  'cat-makeup': 'makeup',
  'cat-photography': 'photography',
  'cat-transport': 'transport',
  'cat-mehandi': 'mehandi',
};

const emptyGroceryItem = () => ({ name: '', category: '', unit: 'kg', unit_price: '', availability: 'in_stock' });
const emptyDJEquipment = () => ({ name: '', description: '', included: true, unit_price: '' });
const emptyDJPackage = () => ({ name: '', duration_hours: 4, price: '', includes: '' });
const emptyMenuItem = () => ({ name: '', category: '', unit_price: '', dietary_options: '' });
const emptyDecorTheme = () => ({ name: '', description: '', price: '' });
const emptyDecorInventory = () => ({ name: '', category: '', rental_price: '', quantity: '' });
const emptyDecorSetup = () => ({ name: '', included: true, price: '' });

const normalizeList = (value) => (Array.isArray(value) ? value : []);

const VendorOnboardingPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [vendor, setVendor] = useState(null);
  const [requirements, setRequirements] = useState(null);
  const [validation, setValidation] = useState(null);
  const [saving, setSaving] = useState(false);

  const [baseForm, setBaseForm] = useState({
    business_name: '',
    owner_name: '',
    city: '',
    description: '',
    price_min: '',
    price_max: '',
  });

  const [groceryItems, setGroceryItems] = useState([emptyGroceryItem()]);
  const [groceryMeta, setGroceryMeta] = useState({ delivery_radius: '', delivery_schedule: '', minimum_order_quantity: '', quality_grade: '' });
  const [djEquipment, setDjEquipment] = useState([emptyDJEquipment()]);
  const [djPackages, setDjPackages] = useState([emptyDJPackage()]);
  const [djCrewSize, setDjCrewSize] = useState('');
  const [djMeta, setDjMeta] = useState({ performance_type: '', genres: '' });
  const [catererMenu, setCatererMenu] = useState([emptyMenuItem()]);
  const [catererPrice, setCatererPrice] = useState('');
  const [catererMeta, setCatererMeta] = useState({ cuisine_specializations: '', dietary_options: '', minimum_order_quantity: '' });
  const [decorThemes, setDecorThemes] = useState([emptyDecorTheme()]);
  const [decorInventory, setDecorInventory] = useState([emptyDecorInventory()]);
  const [decorSetup, setDecorSetup] = useState([emptyDecorSetup()]);
  const [venueMeta, setVenueMeta] = useState({
    venue_types: '',
    amenities: '',
    capacity_min: '',
    capacity_max: '',
    pricing_model: '',
    pricing_options: [{ label: '', unit: 'per_day', price: '' }],
    availability_calendar: '',
    cancellation_policy: '',
    photo_gallery: '',
    floor_plans: '',
    virtual_tour_url: '',
  });
  const [makeupMeta, setMakeupMeta] = useState({
    specializations: '',
    products_used: '',
    travel_charges: '',
    trial_availability: false,
    before_after_gallery: '',
  });
  const [makeupServices, setMakeupServices] = useState([{ name: '', price: '' }]);
  const [photoMeta, setPhotoMeta] = useState({
    photo_services: '',
    equipment_details: '',
    delivery_timeline: '',
    raw_footage_policy: '',
    portfolio_gallery: '',
  });
  const [photoPackages, setPhotoPackages] = useState([{ name: '', hours: 8, price: '', deliverables: '' }]);
  const [transportMeta, setTransportMeta] = useState({
    vehicle_categories: '',
    pricing_structure: '',
    insurance_coverage: '',
    rental_duration_options: '',
    driver_included: false,
    decoration_services: false,
  });
  const [transportVehicles, setTransportVehicles] = useState([{ name: '', category: '', capacity: '', price: '', unit: 'per_day' }]);
  const [mehandiMeta, setMehandiMeta] = useState({
    design_styles: '',
    quality_type: '',
    application_time_estimates: '',
    home_service: false,
    portfolio_gallery: '',
  });
  const [mehandiServices, setMehandiServices] = useState([{ name: '', price: '', unit: 'per_hand' }]);

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    const loadVendor = async () => {
      try {
        const res = await vendorProfile.getMyVendor();
        const v = res.data;
        setVendor(v);
        setBaseForm({
          business_name: v.business_name || '',
          owner_name: v.owner_name || '',
          city: v.city || '',
          description: v.description || '',
          price_min: v.price_min || '',
          price_max: v.price_max || '',
        });
        setGroceryItems(normalizeList(v.grocery_items).length ? v.grocery_items : [emptyGroceryItem()]);
        setGroceryMeta({
          delivery_radius: v.delivery_radius || v.details?.delivery_radius || '',
          delivery_schedule: v.delivery_schedule || v.details?.delivery_schedule || '',
          minimum_order_quantity: v.minimum_order_quantity || v.details?.minimum_order_quantity || '',
          quality_grade: v.quality_grade || v.details?.quality_grade || '',
        });
        setDjEquipment(normalizeList(v.dj_equipment).length ? v.dj_equipment : [emptyDJEquipment()]);
        setDjPackages(normalizeList(v.dj_packages).length ? v.dj_packages : [emptyDJPackage()]);
        setDjCrewSize(v.dj_crew_size || '');
        setDjMeta({
          performance_type: v.performance_type || v.details?.performance_type || '',
          genres: Array.isArray(v.genres) ? v.genres.join(', ') : (v.details?.genres || ''),
        });
        setCatererMenu(normalizeList(v.caterer_menu_items).length ? v.caterer_menu_items : [emptyMenuItem()]);
        setCatererPrice(v.caterer_price_per_plate || '');
        setCatererMeta({
          cuisine_specializations: Array.isArray(v.cuisine_specializations) ? v.cuisine_specializations.join(', ') : (v.details?.cuisine_specializations || ''),
          dietary_options: Array.isArray(v.dietary_options) ? v.dietary_options.join(', ') : (v.details?.dietary_options || ''),
          minimum_order_quantity: v.minimum_order_quantity || v.details?.minimum_order_quantity || '',
        });
        setDecorThemes(normalizeList(v.decorator_themes).length ? v.decorator_themes : [emptyDecorTheme()]);
        setDecorInventory(normalizeList(v.decorator_inventory).length ? v.decorator_inventory : [emptyDecorInventory()]);
        setDecorSetup(normalizeList(v.decorator_setup_types).length ? v.decorator_setup_types : [emptyDecorSetup()]);
        setVenueMeta({
          venue_types: Array.isArray(v.venue_types) ? v.venue_types.join(', ') : (v.details?.venue_types || ''),
          amenities: Array.isArray(v.amenities) ? v.amenities.join(', ') : (v.details?.amenities || ''),
          capacity_min: v.capacity_min || v.details?.capacity_min || '',
          capacity_max: v.capacity_max || v.details?.capacity_max || '',
          pricing_model: v.pricing_model || v.details?.pricing_model || '',
          pricing_options: v.pricing_options?.length ? v.pricing_options : [{ label: '', unit: 'per_day', price: '' }],
          availability_calendar: v.availability_calendar || v.details?.availability_calendar || '',
          cancellation_policy: v.cancellation_policy || v.details?.cancellation_policy || '',
          photo_gallery: Array.isArray(v.photo_gallery) ? v.photo_gallery.join(', ') : (v.details?.photo_gallery || ''),
          floor_plans: Array.isArray(v.floor_plans) ? v.floor_plans.join(', ') : (v.details?.floor_plans || ''),
          virtual_tour_url: v.virtual_tour_url || v.details?.virtual_tour_url || '',
        });
        setMakeupMeta({
          specializations: Array.isArray(v.makeup_specializations) ? v.makeup_specializations.join(', ') : (v.details?.makeup_specializations || ''),
          products_used: Array.isArray(v.products_used) ? v.products_used.join(', ') : (v.details?.products_used || ''),
          travel_charges: v.travel_charges || v.details?.travel_charges || '',
          trial_availability: v.trial_availability ?? v.details?.trial_availability ?? false,
          before_after_gallery: Array.isArray(v.before_after_gallery) ? v.before_after_gallery.join(', ') : (v.details?.before_after_gallery || ''),
        });
        setMakeupServices(v.makeup_services?.length ? v.makeup_services : [{ name: '', price: '' }]);
        setPhotoMeta({
          photo_services: Array.isArray(v.photo_services) ? v.photo_services.join(', ') : (v.details?.photo_services || ''),
          equipment_details: Array.isArray(v.equipment_details) ? v.equipment_details.join(', ') : (v.details?.equipment_details || ''),
          delivery_timeline: v.delivery_timeline || v.details?.delivery_timeline || '',
          raw_footage_policy: v.raw_footage_policy || v.details?.raw_footage_policy || '',
          portfolio_gallery: Array.isArray(v.portfolio_gallery) ? v.portfolio_gallery.join(', ') : (v.details?.portfolio_gallery || ''),
        });
        setPhotoPackages(v.photo_packages?.length ? v.photo_packages : [{ name: '', hours: 8, price: '', deliverables: '' }]);
        setTransportMeta({
          vehicle_categories: Array.isArray(v.vehicle_categories) ? v.vehicle_categories.join(', ') : (v.details?.vehicle_categories || ''),
          pricing_structure: v.pricing_structure || v.details?.pricing_structure || '',
          insurance_coverage: v.insurance_coverage || v.details?.insurance_coverage || '',
          rental_duration_options: Array.isArray(v.rental_duration_options) ? v.rental_duration_options.join(', ') : (v.details?.rental_duration_options || ''),
          driver_included: v.driver_included ?? v.details?.driver_included ?? false,
          decoration_services: v.decoration_services ?? v.details?.decoration_services ?? false,
        });
        setTransportVehicles(v.transport_vehicles?.length ? v.transport_vehicles : [{ name: '', category: '', capacity: '', price: '', unit: 'per_day' }]);
        setMehandiMeta({
          design_styles: Array.isArray(v.design_styles) ? v.design_styles.join(', ') : (v.details?.design_styles || ''),
          quality_type: v.quality_type || v.details?.quality_type || '',
          application_time_estimates: v.application_time_estimates || v.details?.application_time_estimates || '',
          home_service: v.home_service ?? v.details?.home_service ?? false,
          portfolio_gallery: Array.isArray(v.portfolio_gallery) ? v.portfolio_gallery.join(', ') : (v.details?.portfolio_gallery || ''),
        });
        setMehandiServices(v.mehandi_services?.length ? v.mehandi_services : [{ name: '', price: '', unit: 'per_hand' }]);
      } catch (error) {
        const status = error?.response?.status;
        if (status === 404) {
          toast.error('Vendor profile not found. Please complete vendor registration first.');
          navigate('/vendor-register');
          return;
        }
        toast.error('Failed to load vendor profile');
      }
    };
    loadVendor();
  }, [user, navigate]);

  useEffect(() => {
    const section = new URLSearchParams(location.search).get('section');
    if (!section) return;
    const target = document.getElementById(section);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [location.search]);

  const categorySlug = useMemo(() => {
    if (!vendor) return null;
    return CATEGORY_SLUG_MAP[vendor.category_id] || vendor.category_id;
  }, [vendor]);

  useEffect(() => {
    if (!categorySlug) return;
    assistantApi.getRequirements(categorySlug)
      .then((res) => setRequirements(res.data))
      .catch(() => setRequirements(null));
  }, [categorySlug]);

  const buildValidationPayload = useCallback(() => ({
    category_id: categorySlug,
    business_name: baseForm.business_name,
    owner_name: baseForm.owner_name,
    city: baseForm.city,
    price_min: baseForm.price_min ? Number(baseForm.price_min) : null,
    price_max: baseForm.price_max ? Number(baseForm.price_max) : null,
    grocery_items: groceryItems.filter((i) => i.name),
    delivery_radius: groceryMeta.delivery_radius || null,
    delivery_schedule: groceryMeta.delivery_schedule || null,
    minimum_order_quantity: groceryMeta.minimum_order_quantity ? Number(groceryMeta.minimum_order_quantity) : null,
    quality_grade: groceryMeta.quality_grade || null,
    dj_equipment: djEquipment.filter((i) => i.name),
    dj_packages: djPackages.filter((p) => p.name),
    dj_crew_size: djCrewSize ? Number(djCrewSize) : null,
    performance_type: djMeta.performance_type || null,
    genres: djMeta.genres ? djMeta.genres.split(',').map((s) => s.trim()).filter(Boolean) : [],
    caterer_menu_items: catererMenu.filter((i) => i.name),
    caterer_price_per_plate: catererPrice ? Number(catererPrice) : null,
    cuisine_specializations: catererMeta.cuisine_specializations ? catererMeta.cuisine_specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
    dietary_options: catererMeta.dietary_options ? catererMeta.dietary_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
    minimum_order_quantity: catererMeta.minimum_order_quantity ? Number(catererMeta.minimum_order_quantity) : null,
    decorator_themes: decorThemes.filter((t) => t.name),
    decorator_inventory: decorInventory.filter((i) => i.name),
    decorator_setup_types: decorSetup.filter((s) => s.name),
    venue_types: venueMeta.venue_types ? venueMeta.venue_types.split(',').map((s) => s.trim()).filter(Boolean) : [],
    amenities: venueMeta.amenities ? venueMeta.amenities.split(',').map((s) => s.trim()).filter(Boolean) : [],
    capacity_min: venueMeta.capacity_min ? Number(venueMeta.capacity_min) : null,
    capacity_max: venueMeta.capacity_max ? Number(venueMeta.capacity_max) : null,
    pricing_model: venueMeta.pricing_model || null,
    pricing_options: (venueMeta.pricing_options || []).filter((p) => p.label).map((p) => ({
      ...p,
      price: Number(p.price || 0),
    })),
    availability_calendar: venueMeta.availability_calendar || null,
    cancellation_policy: venueMeta.cancellation_policy || null,
    photo_gallery: venueMeta.photo_gallery ? venueMeta.photo_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
    floor_plans: venueMeta.floor_plans ? venueMeta.floor_plans.split(',').map((s) => s.trim()).filter(Boolean) : [],
    virtual_tour_url: venueMeta.virtual_tour_url || null,
    makeup_specializations: makeupMeta.specializations ? makeupMeta.specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
    makeup_services: makeupServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
    before_after_gallery: makeupMeta.before_after_gallery ? makeupMeta.before_after_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
    products_used: makeupMeta.products_used ? makeupMeta.products_used.split(',').map((s) => s.trim()).filter(Boolean) : [],
    travel_charges: makeupMeta.travel_charges || null,
    trial_availability: !!makeupMeta.trial_availability,
    photo_services: photoMeta.photo_services ? photoMeta.photo_services.split(',').map((s) => s.trim()).filter(Boolean) : [],
    photo_packages: photoPackages.filter((p) => p.name).map((p) => ({
      ...p,
      hours: Number(p.hours || 0),
      price: Number(p.price || 0),
      deliverables: p.deliverables ? p.deliverables.split(',').map((s) => s.trim()).filter(Boolean) : [],
    })),
    equipment_details: photoMeta.equipment_details ? photoMeta.equipment_details.split(',').map((s) => s.trim()).filter(Boolean) : [],
    delivery_timeline: photoMeta.delivery_timeline || null,
    raw_footage_policy: photoMeta.raw_footage_policy || null,
    portfolio_gallery: photoMeta.portfolio_gallery ? photoMeta.portfolio_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
    transport_vehicles: transportVehicles.filter((v) => v.name).map((v) => ({
      ...v,
      capacity: v.capacity ? Number(v.capacity) : null,
      price: v.price ? Number(v.price) : null,
    })),
    vehicle_categories: transportMeta.vehicle_categories ? transportMeta.vehicle_categories.split(',').map((s) => s.trim()).filter(Boolean) : [],
    pricing_structure: transportMeta.pricing_structure || null,
    insurance_coverage: transportMeta.insurance_coverage || null,
    rental_duration_options: transportMeta.rental_duration_options ? transportMeta.rental_duration_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
    driver_included: !!transportMeta.driver_included,
    decoration_services: !!transportMeta.decoration_services,
    design_styles: mehandiMeta.design_styles ? mehandiMeta.design_styles.split(',').map((s) => s.trim()).filter(Boolean) : [],
    mehandi_services: mehandiServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
    quality_type: mehandiMeta.quality_type || null,
    application_time_estimates: mehandiMeta.application_time_estimates || null,
    home_service: !!mehandiMeta.home_service,
    portfolio_gallery: mehandiMeta.portfolio_gallery ? mehandiMeta.portfolio_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
  }), [
    categorySlug,
    baseForm,
    groceryItems,
    groceryMeta,
    djEquipment,
    djPackages,
    djCrewSize,
    djMeta,
    catererMenu,
    catererPrice,
    catererMeta,
    decorThemes,
    decorInventory,
    decorSetup,
    venueMeta,
    makeupMeta,
    makeupServices,
    photoMeta,
    photoPackages,
    transportVehicles,
    transportMeta,
    mehandiMeta,
    mehandiServices,
  ]);

  const handleValidate = useCallback(async () => {
    try {
      const res = await assistantApi.validateOnboarding(buildValidationPayload());
      setValidation(res.data);
    } catch (error) {
      toast.error('Unable to validate onboarding');
    }
  }, [buildValidationPayload]);

  useEffect(() => {
    if (vendor) {
      handleValidate();
    }
  }, [vendor, categorySlug, handleValidate]);

  const progress = useMemo(() => {
    if (!validation) return 0;
    const total = (validation.required || []).length || 1;
    const missing = validation.missing_required?.length || 0;
    return Math.round(((total - missing) / total) * 100);
  }, [validation]);

  const handleSave = async () => {
    if (!vendor) return;
    setSaving(true);
    try {
      const payload = {
        business_name: baseForm.business_name,
        owner_name: baseForm.owner_name,
        city: baseForm.city,
        description: baseForm.description,
        price_min: baseForm.price_min ? Number(baseForm.price_min) : null,
        price_max: baseForm.price_max ? Number(baseForm.price_max) : null,
        grocery_items: groceryItems.filter((i) => i.name),
        delivery_radius: groceryMeta.delivery_radius || null,
        delivery_schedule: groceryMeta.delivery_schedule || null,
        minimum_order_quantity: groceryMeta.minimum_order_quantity ? Number(groceryMeta.minimum_order_quantity) : null,
        quality_grade: groceryMeta.quality_grade || null,
        dj_equipment: djEquipment.filter((i) => i.name),
        dj_packages: djPackages
          .filter((p) => p.name)
          .map((p) => ({
            ...p,
            duration_hours: Number(p.duration_hours || 0),
            price: Number(p.price || 0),
            includes: p.includes ? p.includes.split(',').map((s) => s.trim()).filter(Boolean) : [],
          })),
        dj_crew_size: djCrewSize ? Number(djCrewSize) : null,
        performance_type: djMeta.performance_type || null,
        genres: djMeta.genres ? djMeta.genres.split(',').map((s) => s.trim()).filter(Boolean) : [],
        caterer_menu_items: catererMenu
          .filter((i) => i.name)
          .map((i) => ({
            ...i,
            unit_price: Number(i.unit_price || 0),
            dietary_options: i.dietary_options ? i.dietary_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
          })),
        caterer_price_per_plate: catererPrice ? Number(catererPrice) : null,
        cuisine_specializations: catererMeta.cuisine_specializations ? catererMeta.cuisine_specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
        dietary_options: catererMeta.dietary_options ? catererMeta.dietary_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
        minimum_order_quantity: catererMeta.minimum_order_quantity ? Number(catererMeta.minimum_order_quantity) : null,
        decorator_themes: decorThemes
          .filter((t) => t.name)
          .map((t) => ({ ...t, price: t.price ? Number(t.price) : null })),
        decorator_inventory: decorInventory
          .filter((i) => i.name)
          .map((i) => ({
            ...i,
            rental_price: i.rental_price ? Number(i.rental_price) : null,
            quantity: i.quantity ? Number(i.quantity) : null,
          })),
        decorator_setup_types: decorSetup
          .filter((s) => s.name)
          .map((s) => ({ ...s, price: s.price ? Number(s.price) : null })),
        venue_types: venueMeta.venue_types ? venueMeta.venue_types.split(',').map((s) => s.trim()).filter(Boolean) : [],
        amenities: venueMeta.amenities ? venueMeta.amenities.split(',').map((s) => s.trim()).filter(Boolean) : [],
        capacity_min: venueMeta.capacity_min ? Number(venueMeta.capacity_min) : null,
        capacity_max: venueMeta.capacity_max ? Number(venueMeta.capacity_max) : null,
        pricing_model: venueMeta.pricing_model || null,
        pricing_options: (venueMeta.pricing_options || []).filter((p) => p.label).map((p) => ({
          ...p,
          price: Number(p.price || 0),
        })),
        availability_calendar: venueMeta.availability_calendar || null,
        cancellation_policy: venueMeta.cancellation_policy || null,
        photo_gallery: venueMeta.photo_gallery ? venueMeta.photo_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
        floor_plans: venueMeta.floor_plans ? venueMeta.floor_plans.split(',').map((s) => s.trim()).filter(Boolean) : [],
        virtual_tour_url: venueMeta.virtual_tour_url || null,
        makeup_specializations: makeupMeta.specializations ? makeupMeta.specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
        makeup_services: makeupServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
        before_after_gallery: makeupMeta.before_after_gallery ? makeupMeta.before_after_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
        products_used: makeupMeta.products_used ? makeupMeta.products_used.split(',').map((s) => s.trim()).filter(Boolean) : [],
        travel_charges: makeupMeta.travel_charges || null,
        trial_availability: !!makeupMeta.trial_availability,
        photo_services: photoMeta.photo_services ? photoMeta.photo_services.split(',').map((s) => s.trim()).filter(Boolean) : [],
        photo_packages: photoPackages.filter((p) => p.name).map((p) => ({
          ...p,
          hours: Number(p.hours || 0),
          price: Number(p.price || 0),
          deliverables: p.deliverables ? p.deliverables.split(',').map((s) => s.trim()).filter(Boolean) : [],
        })),
        equipment_details: photoMeta.equipment_details ? photoMeta.equipment_details.split(',').map((s) => s.trim()).filter(Boolean) : [],
        delivery_timeline: photoMeta.delivery_timeline || null,
        raw_footage_policy: photoMeta.raw_footage_policy || null,
        portfolio_gallery: photoMeta.portfolio_gallery ? photoMeta.portfolio_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
        transport_vehicles: transportVehicles.filter((v) => v.name).map((v) => ({
          ...v,
          capacity: v.capacity ? Number(v.capacity) : null,
          price: v.price ? Number(v.price) : null,
        })),
        vehicle_categories: transportMeta.vehicle_categories ? transportMeta.vehicle_categories.split(',').map((s) => s.trim()).filter(Boolean) : [],
        pricing_structure: transportMeta.pricing_structure || null,
        insurance_coverage: transportMeta.insurance_coverage || null,
        rental_duration_options: transportMeta.rental_duration_options ? transportMeta.rental_duration_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
        driver_included: !!transportMeta.driver_included,
        decoration_services: !!transportMeta.decoration_services,
        design_styles: mehandiMeta.design_styles ? mehandiMeta.design_styles.split(',').map((s) => s.trim()).filter(Boolean) : [],
        mehandi_services: mehandiServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0), unit: s.unit || 'per_hand' })),
        quality_type: mehandiMeta.quality_type || null,
        application_time_estimates: mehandiMeta.application_time_estimates || null,
        home_service: !!mehandiMeta.home_service,
        portfolio_gallery: mehandiMeta.portfolio_gallery ? mehandiMeta.portfolio_gallery.split(',').map((s) => s.trim()).filter(Boolean) : [],
      };

      const res = await vendorsApi.updateOnboarding(vendor.id, payload);
      setVendor(res.data.vendor);
      setValidation(res.data.onboarding);
      toast.success('Onboarding updated');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update onboarding');
    } finally {
      setSaving(false);
    }
  };

  if (!vendor) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500">Loading onboarding...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-4xl font-semibold">Complete Your Onboarding</h1>
          <p className="text-stone-600 mt-2">Finish the missing details to get approved faster.</p>
        </div>

        <Card className="p-6 bg-white rounded-2xl border border-stone-100">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <p className="text-sm uppercase tracking-wide text-stone-500">Progress</p>
              <p className="text-2xl font-semibold text-stone-900">{progress}% Complete</p>
            </div>
            <div className="flex-1 min-w-[200px]">
              <div className="h-2 rounded-full bg-stone-100">
                <div className="h-2 rounded-full bg-primary" style={{ width: `${progress}%` }} />
              </div>
            </div>
            <Button onClick={handleValidate} variant="outline">Refresh Checklist</Button>
          </div>
          {validation?.missing_required?.length > 0 && (
            <div className="mt-4 text-sm text-amber-700">
              Missing required: {validation.missing_required.join(', ')}
            </div>
          )}
        </Card>

        {requirements && (
          <Card className="p-6 bg-white rounded-2xl border border-stone-100">
            <h2 className="text-xl font-semibold mb-4">Onboarding Checklist</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(requirements.required || []).map((field) => (
                <div key={field} className="flex items-center gap-3">
                  <span className={`w-3 h-3 rounded-full ${validation?.missing_required?.includes(field) ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                  <span className="text-sm text-stone-700">{field}</span>
                </div>
              ))}
            </div>
            {(requirements.recommended || []).length > 0 && (
              <div className="mt-4 text-sm text-stone-500">
                Recommended: {(requirements.recommended || []).join(', ')}
              </div>
            )}
          </Card>
        )}

        <Card id="core" className="p-6 bg-white rounded-2xl border border-stone-100">
          <h2 className="text-xl font-semibold mb-4">Core Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Business Name</Label>
              <Input value={baseForm.business_name} onChange={(e) => setBaseForm({ ...baseForm, business_name: e.target.value })} />
            </div>
            <div>
              <Label>Owner Name</Label>
              <Input value={baseForm.owner_name} onChange={(e) => setBaseForm({ ...baseForm, owner_name: e.target.value })} />
            </div>
            <div>
              <Label>City</Label>
              <Input value={baseForm.city} onChange={(e) => setBaseForm({ ...baseForm, city: e.target.value })} />
            </div>
            <div>
              <Label>Starting Price Min</Label>
              <Input type="number" value={baseForm.price_min} onChange={(e) => setBaseForm({ ...baseForm, price_min: e.target.value })} />
            </div>
            <div>
              <Label>Starting Price Max</Label>
              <Input type="number" value={baseForm.price_max} onChange={(e) => setBaseForm({ ...baseForm, price_max: e.target.value })} />
            </div>
          </div>
          <div className="mt-4">
            <Label>Description</Label>
            <Textarea value={baseForm.description} onChange={(e) => setBaseForm({ ...baseForm, description: e.target.value })} rows={4} />
          </div>
        </Card>

        {categorySlug === 'grocery' && (
          <Card id="grocery" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Grocery Catalog</h2>
              <p className="text-sm text-stone-500">Add items with unit pricing and availability.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Delivery radius" value={groceryMeta.delivery_radius} onChange={(e) => setGroceryMeta({ ...groceryMeta, delivery_radius: e.target.value })} />
              <Input placeholder="Delivery schedule" value={groceryMeta.delivery_schedule} onChange={(e) => setGroceryMeta({ ...groceryMeta, delivery_schedule: e.target.value })} />
              <Input type="number" placeholder="Minimum order quantity" value={groceryMeta.minimum_order_quantity} onChange={(e) => setGroceryMeta({ ...groceryMeta, minimum_order_quantity: e.target.value })} />
              <Input placeholder="Quality grade" value={groceryMeta.quality_grade} onChange={(e) => setGroceryMeta({ ...groceryMeta, quality_grade: e.target.value })} />
            </div>
            {groceryItems.map((item, idx) => (
              <div key={`grocery-${idx}`} className="grid grid-cols-1 md:grid-cols-5 gap-3">
                <Input placeholder="Item name" value={item.name} onChange={(e) => {
                  const next = [...groceryItems];
                  next[idx].name = e.target.value;
                  setGroceryItems(next);
                }} />
                <Input placeholder="Category" value={item.category} onChange={(e) => {
                  const next = [...groceryItems];
                  next[idx].category = e.target.value;
                  setGroceryItems(next);
                }} />
                <Input placeholder="Unit" value={item.unit} onChange={(e) => {
                  const next = [...groceryItems];
                  next[idx].unit = e.target.value;
                  setGroceryItems(next);
                }} />
                <Input type="number" placeholder="Unit price" value={item.unit_price} onChange={(e) => {
                  const next = [...groceryItems];
                  next[idx].unit_price = e.target.value;
                  setGroceryItems(next);
                }} />
                <Input placeholder="Availability" value={item.availability} onChange={(e) => {
                  const next = [...groceryItems];
                  next[idx].availability = e.target.value;
                  setGroceryItems(next);
                }} />
              </div>
            ))}
            <Button variant="outline" onClick={() => setGroceryItems([...groceryItems, emptyGroceryItem()])}>Add Item</Button>
          </Card>
        )}

        {categorySlug === 'entertainment' && (
          <Card id="entertainment" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-6">
            <div>
              <h2 className="text-xl font-semibold">DJ / Entertainment Setup</h2>
              <p className="text-sm text-stone-500">List equipment and performance packages.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Performance type" value={djMeta.performance_type} onChange={(e) => setDjMeta({ ...djMeta, performance_type: e.target.value })} />
              <Input placeholder="Genres (comma separated)" value={djMeta.genres} onChange={(e) => setDjMeta({ ...djMeta, genres: e.target.value })} />
            </div>
            <div>
              <Label>Crew Size</Label>
              <Input type="number" value={djCrewSize} onChange={(e) => setDjCrewSize(e.target.value)} />
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Equipment</p>
              {djEquipment.map((item, idx) => (
                <div key={`dj-eq-${idx}`} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input placeholder="Equipment name" value={item.name} onChange={(e) => {
                    const next = [...djEquipment];
                    next[idx].name = e.target.value;
                    setDjEquipment(next);
                  }} />
                  <Input placeholder="Description" value={item.description} onChange={(e) => {
                    const next = [...djEquipment];
                    next[idx].description = e.target.value;
                    setDjEquipment(next);
                  }} />
                  <Input placeholder="Unit price" type="number" value={item.unit_price} onChange={(e) => {
                    const next = [...djEquipment];
                    next[idx].unit_price = e.target.value;
                    setDjEquipment(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setDjEquipment([...djEquipment, emptyDJEquipment()])}>Add Equipment</Button>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Performance Packages</p>
              {djPackages.map((pkg, idx) => (
                <div key={`dj-pkg-${idx}`} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <Input placeholder="Package name" value={pkg.name} onChange={(e) => {
                    const next = [...djPackages];
                    next[idx].name = e.target.value;
                    setDjPackages(next);
                  }} />
                  <Input type="number" placeholder="Hours" value={pkg.duration_hours} onChange={(e) => {
                    const next = [...djPackages];
                    next[idx].duration_hours = e.target.value;
                    setDjPackages(next);
                  }} />
                  <Input type="number" placeholder="Price" value={pkg.price} onChange={(e) => {
                    const next = [...djPackages];
                    next[idx].price = e.target.value;
                    setDjPackages(next);
                  }} />
                  <Input placeholder="Includes (comma)" value={pkg.includes} onChange={(e) => {
                    const next = [...djPackages];
                    next[idx].includes = e.target.value;
                    setDjPackages(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setDjPackages([...djPackages, emptyDJPackage()])}>Add Package</Button>
            </div>
          </Card>
        )}

        {categorySlug === 'catering' && (
          <Card id="catering" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Catering Menu</h2>
              <p className="text-sm text-stone-500">Add menu items with per-plate pricing.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Cuisine specializations" value={catererMeta.cuisine_specializations} onChange={(e) => setCatererMeta({ ...catererMeta, cuisine_specializations: e.target.value })} />
              <Input placeholder="Dietary options" value={catererMeta.dietary_options} onChange={(e) => setCatererMeta({ ...catererMeta, dietary_options: e.target.value })} />
              <Input type="number" placeholder="Minimum order quantity" value={catererMeta.minimum_order_quantity} onChange={(e) => setCatererMeta({ ...catererMeta, minimum_order_quantity: e.target.value })} />
            </div>
            <div>
              <Label>Per-Plate Starting Price</Label>
              <Input type="number" value={catererPrice} onChange={(e) => setCatererPrice(e.target.value)} />
            </div>
            {catererMenu.map((item, idx) => (
              <div key={`menu-${idx}`} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <Input placeholder="Menu item" value={item.name} onChange={(e) => {
                  const next = [...catererMenu];
                  next[idx].name = e.target.value;
                  setCatererMenu(next);
                }} />
                <Input placeholder="Category" value={item.category} onChange={(e) => {
                  const next = [...catererMenu];
                  next[idx].category = e.target.value;
                  setCatererMenu(next);
                }} />
                <Input type="number" placeholder="Price" value={item.unit_price} onChange={(e) => {
                  const next = [...catererMenu];
                  next[idx].unit_price = e.target.value;
                  setCatererMenu(next);
                }} />
                <Input placeholder="Dietary options" value={item.dietary_options} onChange={(e) => {
                  const next = [...catererMenu];
                  next[idx].dietary_options = e.target.value;
                  setCatererMenu(next);
                }} />
              </div>
            ))}
            <Button variant="outline" onClick={() => setCatererMenu([...catererMenu, emptyMenuItem()])}>Add Menu Item</Button>
          </Card>
        )}

        {categorySlug === 'decor' && (
          <Card id="decor" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-6">
            <div>
              <h2 className="text-xl font-semibold">Decor Themes & Inventory</h2>
              <p className="text-sm text-stone-500">Showcase themes, inventory, and setup types.</p>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Themes</p>
              {decorThemes.map((theme, idx) => (
                <div key={`theme-${idx}`} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input placeholder="Theme name" value={theme.name} onChange={(e) => {
                    const next = [...decorThemes];
                    next[idx].name = e.target.value;
                    setDecorThemes(next);
                  }} />
                  <Input placeholder="Description" value={theme.description} onChange={(e) => {
                    const next = [...decorThemes];
                    next[idx].description = e.target.value;
                    setDecorThemes(next);
                  }} />
                  <Input type="number" placeholder="Price" value={theme.price} onChange={(e) => {
                    const next = [...decorThemes];
                    next[idx].price = e.target.value;
                    setDecorThemes(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setDecorThemes([...decorThemes, emptyDecorTheme()])}>Add Theme</Button>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Inventory</p>
              {decorInventory.map((item, idx) => (
                <div key={`inv-${idx}`} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <Input placeholder="Item" value={item.name} onChange={(e) => {
                    const next = [...decorInventory];
                    next[idx].name = e.target.value;
                    setDecorInventory(next);
                  }} />
                  <Input placeholder="Category" value={item.category} onChange={(e) => {
                    const next = [...decorInventory];
                    next[idx].category = e.target.value;
                    setDecorInventory(next);
                  }} />
                  <Input type="number" placeholder="Rental price" value={item.rental_price} onChange={(e) => {
                    const next = [...decorInventory];
                    next[idx].rental_price = e.target.value;
                    setDecorInventory(next);
                  }} />
                  <Input type="number" placeholder="Quantity" value={item.quantity} onChange={(e) => {
                    const next = [...decorInventory];
                    next[idx].quantity = e.target.value;
                    setDecorInventory(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setDecorInventory([...decorInventory, emptyDecorInventory()])}>Add Inventory Item</Button>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Setup Types</p>
              {decorSetup.map((item, idx) => (
                <div key={`setup-${idx}`} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input placeholder="Setup name" value={item.name} onChange={(e) => {
                    const next = [...decorSetup];
                    next[idx].name = e.target.value;
                    setDecorSetup(next);
                  }} />
                  <Input placeholder="Included (true/false)" value={item.included ? 'true' : 'false'} onChange={(e) => {
                    const next = [...decorSetup];
                    next[idx].included = e.target.value === 'true';
                    setDecorSetup(next);
                  }} />
                  <Input type="number" placeholder="Price" value={item.price} onChange={(e) => {
                    const next = [...decorSetup];
                    next[idx].price = e.target.value;
                    setDecorSetup(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setDecorSetup([...decorSetup, emptyDecorSetup()])}>Add Setup Type</Button>
            </div>
          </Card>
        )}

        {categorySlug === 'venues' && (
          <Card id="venues" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Venue Details</h2>
              <p className="text-sm text-stone-500">Share venue capacity, amenities, and pricing.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Venue types" value={venueMeta.venue_types} onChange={(e) => setVenueMeta({ ...venueMeta, venue_types: e.target.value })} />
              <Input placeholder="Amenities" value={venueMeta.amenities} onChange={(e) => setVenueMeta({ ...venueMeta, amenities: e.target.value })} />
              <Input type="number" placeholder="Capacity min" value={venueMeta.capacity_min} onChange={(e) => setVenueMeta({ ...venueMeta, capacity_min: e.target.value })} />
              <Input type="number" placeholder="Capacity max" value={venueMeta.capacity_max} onChange={(e) => setVenueMeta({ ...venueMeta, capacity_max: e.target.value })} />
              <Input placeholder="Pricing model" value={venueMeta.pricing_model} onChange={(e) => setVenueMeta({ ...venueMeta, pricing_model: e.target.value })} />
              <Input placeholder="Availability calendar" value={venueMeta.availability_calendar} onChange={(e) => setVenueMeta({ ...venueMeta, availability_calendar: e.target.value })} />
              <Input placeholder="Cancellation policy" value={venueMeta.cancellation_policy} onChange={(e) => setVenueMeta({ ...venueMeta, cancellation_policy: e.target.value })} />
              <Input placeholder="Photo gallery URLs" value={venueMeta.photo_gallery} onChange={(e) => setVenueMeta({ ...venueMeta, photo_gallery: e.target.value })} />
              <Input placeholder="Floor plan URLs" value={venueMeta.floor_plans} onChange={(e) => setVenueMeta({ ...venueMeta, floor_plans: e.target.value })} />
              <Input placeholder="Virtual tour URL" value={venueMeta.virtual_tour_url} onChange={(e) => setVenueMeta({ ...venueMeta, virtual_tour_url: e.target.value })} />
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Pricing Options</p>
              {(venueMeta.pricing_options || []).map((opt, idx) => (
                <div key={`venue-pricing-${idx}`} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input placeholder="Label" value={opt.label} onChange={(e) => {
                    const next = [...venueMeta.pricing_options];
                    next[idx].label = e.target.value;
                    setVenueMeta({ ...venueMeta, pricing_options: next });
                  }} />
                  <Input placeholder="Unit (per_day/per_event)" value={opt.unit} onChange={(e) => {
                    const next = [...venueMeta.pricing_options];
                    next[idx].unit = e.target.value;
                    setVenueMeta({ ...venueMeta, pricing_options: next });
                  }} />
                  <Input type="number" placeholder="Price" value={opt.price} onChange={(e) => {
                    const next = [...venueMeta.pricing_options];
                    next[idx].price = e.target.value;
                    setVenueMeta({ ...venueMeta, pricing_options: next });
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setVenueMeta({ ...venueMeta, pricing_options: [...venueMeta.pricing_options, { label: '', unit: 'per_day', price: '' }] })}>Add Pricing Option</Button>
            </div>
          </Card>
        )}

        {categorySlug === 'makeup' && (
          <Card id="makeup" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Makeup Services</h2>
              <p className="text-sm text-stone-500">List specializations, services, and products used.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Specializations" value={makeupMeta.specializations} onChange={(e) => setMakeupMeta({ ...makeupMeta, specializations: e.target.value })} />
              <Input placeholder="Products used" value={makeupMeta.products_used} onChange={(e) => setMakeupMeta({ ...makeupMeta, products_used: e.target.value })} />
              <Input placeholder="Travel charges" value={makeupMeta.travel_charges} onChange={(e) => setMakeupMeta({ ...makeupMeta, travel_charges: e.target.value })} />
              <Input placeholder="Before/after gallery URLs" value={makeupMeta.before_after_gallery} onChange={(e) => setMakeupMeta({ ...makeupMeta, before_after_gallery: e.target.value })} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!makeupMeta.trial_availability} onChange={(e) => setMakeupMeta({ ...makeupMeta, trial_availability: e.target.checked })} />
              Trial availability
            </label>
            <div className="space-y-3">
              <p className="text-sm font-medium">Service Menu</p>
              {makeupServices.map((svc, idx) => (
                <div key={`makeup-${idx}`} className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Input placeholder="Service name" value={svc.name} onChange={(e) => {
                    const next = [...makeupServices];
                    next[idx].name = e.target.value;
                    setMakeupServices(next);
                  }} />
                  <Input type="number" placeholder="Price" value={svc.price} onChange={(e) => {
                    const next = [...makeupServices];
                    next[idx].price = e.target.value;
                    setMakeupServices(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setMakeupServices([...makeupServices, { name: '', price: '' }])}>Add Service</Button>
            </div>
          </Card>
        )}

        {categorySlug === 'photography' && (
          <Card id="photography" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Photography & Videography</h2>
              <p className="text-sm text-stone-500">Capture deliverables, packages, and timelines.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Services" value={photoMeta.photo_services} onChange={(e) => setPhotoMeta({ ...photoMeta, photo_services: e.target.value })} />
              <Input placeholder="Equipment details" value={photoMeta.equipment_details} onChange={(e) => setPhotoMeta({ ...photoMeta, equipment_details: e.target.value })} />
              <Input placeholder="Delivery timeline" value={photoMeta.delivery_timeline} onChange={(e) => setPhotoMeta({ ...photoMeta, delivery_timeline: e.target.value })} />
              <Input placeholder="Raw footage policy" value={photoMeta.raw_footage_policy} onChange={(e) => setPhotoMeta({ ...photoMeta, raw_footage_policy: e.target.value })} />
              <Input placeholder="Portfolio gallery URLs" value={photoMeta.portfolio_gallery} onChange={(e) => setPhotoMeta({ ...photoMeta, portfolio_gallery: e.target.value })} />
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium">Packages</p>
              {photoPackages.map((pkg, idx) => (
                <div key={`photo-${idx}`} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <Input placeholder="Package name" value={pkg.name} onChange={(e) => {
                    const next = [...photoPackages];
                    next[idx].name = e.target.value;
                    setPhotoPackages(next);
                  }} />
                  <Input type="number" placeholder="Hours" value={pkg.hours} onChange={(e) => {
                    const next = [...photoPackages];
                    next[idx].hours = e.target.value;
                    setPhotoPackages(next);
                  }} />
                  <Input type="number" placeholder="Price" value={pkg.price} onChange={(e) => {
                    const next = [...photoPackages];
                    next[idx].price = e.target.value;
                    setPhotoPackages(next);
                  }} />
                  <Input placeholder="Deliverables" value={pkg.deliverables} onChange={(e) => {
                    const next = [...photoPackages];
                    next[idx].deliverables = e.target.value;
                    setPhotoPackages(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setPhotoPackages([...photoPackages, { name: '', hours: 8, price: '', deliverables: '' }])}>Add Package</Button>
            </div>
          </Card>
        )}

        {categorySlug === 'transport' && (
          <Card id="transport" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Transport & Rentals</h2>
              <p className="text-sm text-stone-500">Add vehicles and rental options.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Vehicle categories" value={transportMeta.vehicle_categories} onChange={(e) => setTransportMeta({ ...transportMeta, vehicle_categories: e.target.value })} />
              <Input placeholder="Pricing structure" value={transportMeta.pricing_structure} onChange={(e) => setTransportMeta({ ...transportMeta, pricing_structure: e.target.value })} />
              <Input placeholder="Insurance coverage" value={transportMeta.insurance_coverage} onChange={(e) => setTransportMeta({ ...transportMeta, insurance_coverage: e.target.value })} />
              <Input placeholder="Rental duration options" value={transportMeta.rental_duration_options} onChange={(e) => setTransportMeta({ ...transportMeta, rental_duration_options: e.target.value })} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!transportMeta.driver_included} onChange={(e) => setTransportMeta({ ...transportMeta, driver_included: e.target.checked })} />
              Driver included
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!transportMeta.decoration_services} onChange={(e) => setTransportMeta({ ...transportMeta, decoration_services: e.target.checked })} />
              Decoration services
            </label>
            <div className="space-y-3">
              <p className="text-sm font-medium">Fleet</p>
              {transportVehicles.map((veh, idx) => (
                <div key={`vehicle-${idx}`} className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  <Input placeholder="Vehicle name" value={veh.name} onChange={(e) => {
                    const next = [...transportVehicles];
                    next[idx].name = e.target.value;
                    setTransportVehicles(next);
                  }} />
                  <Input placeholder="Category" value={veh.category} onChange={(e) => {
                    const next = [...transportVehicles];
                    next[idx].category = e.target.value;
                    setTransportVehicles(next);
                  }} />
                  <Input type="number" placeholder="Capacity" value={veh.capacity} onChange={(e) => {
                    const next = [...transportVehicles];
                    next[idx].capacity = e.target.value;
                    setTransportVehicles(next);
                  }} />
                  <Input type="number" placeholder="Price" value={veh.price} onChange={(e) => {
                    const next = [...transportVehicles];
                    next[idx].price = e.target.value;
                    setTransportVehicles(next);
                  }} />
                  <Input placeholder="Unit" value={veh.unit} onChange={(e) => {
                    const next = [...transportVehicles];
                    next[idx].unit = e.target.value;
                    setTransportVehicles(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setTransportVehicles([...transportVehicles, { name: '', category: '', capacity: '', price: '', unit: 'per_day' }])}>Add Vehicle</Button>
            </div>
          </Card>
        )}

        {categorySlug === 'mehandi' && (
          <Card id="mehandi" className="p-6 bg-white rounded-2xl border border-stone-100 space-y-4">
            <div>
              <h2 className="text-xl font-semibold">Mehandi Services</h2>
              <p className="text-sm text-stone-500">Showcase design styles and packages.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Design styles" value={mehandiMeta.design_styles} onChange={(e) => setMehandiMeta({ ...mehandiMeta, design_styles: e.target.value })} />
              <Input placeholder="Quality type" value={mehandiMeta.quality_type} onChange={(e) => setMehandiMeta({ ...mehandiMeta, quality_type: e.target.value })} />
              <Input placeholder="Application time estimates" value={mehandiMeta.application_time_estimates} onChange={(e) => setMehandiMeta({ ...mehandiMeta, application_time_estimates: e.target.value })} />
              <Input placeholder="Portfolio gallery URLs" value={mehandiMeta.portfolio_gallery} onChange={(e) => setMehandiMeta({ ...mehandiMeta, portfolio_gallery: e.target.value })} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!mehandiMeta.home_service} onChange={(e) => setMehandiMeta({ ...mehandiMeta, home_service: e.target.checked })} />
              Home service available
            </label>
            <div className="space-y-3">
              <p className="text-sm font-medium">Service Packages</p>
              {mehandiServices.map((svc, idx) => (
                <div key={`mehandi-${idx}`} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input placeholder="Service name" value={svc.name} onChange={(e) => {
                    const next = [...mehandiServices];
                    next[idx].name = e.target.value;
                    setMehandiServices(next);
                  }} />
                  <Input type="number" placeholder="Price" value={svc.price} onChange={(e) => {
                    const next = [...mehandiServices];
                    next[idx].price = e.target.value;
                    setMehandiServices(next);
                  }} />
                  <Input placeholder="Unit" value={svc.unit} onChange={(e) => {
                    const next = [...mehandiServices];
                    next[idx].unit = e.target.value;
                    setMehandiServices(next);
                  }} />
                </div>
              ))}
              <Button variant="outline" onClick={() => setMehandiServices([...mehandiServices, { name: '', price: '', unit: 'per_hand' }])}>Add Service</Button>
            </div>
          </Card>
        )}

        <div className="flex flex-wrap gap-3">
          <Button onClick={handleSave} className="bg-primary hover:bg-primary/90" disabled={saving}>
            {saving ? 'Saving...' : 'Save Onboarding'}
          </Button>
          <Button variant="outline" onClick={() => navigate('/vendor-dashboard')}>Back to Dashboard</Button>
        </div>
      </div>
    </div>
  );
};

export default VendorOnboardingPage;
