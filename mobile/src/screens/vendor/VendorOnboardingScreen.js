import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Card, Title, Paragraph, TextInput, Button, Chip } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { vendors, assistant } from '../../services/api';

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

const VendorOnboardingScreen = () => {
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

  const [groceryItems, setGroceryItems] = useState([{ name: '', unit: 'kg', unit_price: '' }]);
  const [groceryMeta, setGroceryMeta] = useState({ delivery_radius: '', delivery_schedule: '' });
  const [djEquipment, setDjEquipment] = useState([{ name: '', unit_price: '' }]);
  const [djPackages, setDjPackages] = useState([{ name: '', duration_hours: 4, price: '' }]);
  const [djMeta, setDjMeta] = useState({ performance_type: '', genres: '' });
  const [catererMenu, setCatererMenu] = useState([{ name: '', unit_price: '' }]);
  const [catererMeta, setCatererMeta] = useState({ cuisine_specializations: '', dietary_options: '' });
  const [decorThemes, setDecorThemes] = useState([{ name: '', price: '' }]);
  const [venueMeta, setVenueMeta] = useState({ venue_types: '', amenities: '', capacity_min: '', capacity_max: '', pricing_model: '', availability_calendar: '', cancellation_policy: '' });
  const [makeupMeta, setMakeupMeta] = useState({ specializations: '', products_used: '', travel_charges: '' });
  const [makeupServices, setMakeupServices] = useState([{ name: '', price: '' }]);
  const [photoMeta, setPhotoMeta] = useState({ photo_services: '', equipment_details: '', delivery_timeline: '', raw_footage_policy: '' });
  const [photoPackages, setPhotoPackages] = useState([{ name: '', hours: 8, price: '' }]);
  const [transportMeta, setTransportMeta] = useState({ vehicle_categories: '', pricing_structure: '', insurance_coverage: '' });
  const [transportVehicles, setTransportVehicles] = useState([{ name: '', capacity: '', price: '' }]);
  const [mehandiMeta, setMehandiMeta] = useState({ design_styles: '', quality_type: '', application_time_estimates: '' });
  const [mehandiServices, setMehandiServices] = useState([{ name: '', price: '' }]);

  useEffect(() => {
    if (!user?.vendor_id) return;
    const loadVendor = async () => {
      const res = await vendors.getById(user.vendor_id);
      const v = res.data;
      setVendor(v);
      setBaseForm({
        business_name: v.business_name || '',
        owner_name: v.owner_name || '',
        city: v.city || '',
        description: v.description || '',
        price_min: v.price_min ? String(v.price_min) : '',
        price_max: v.price_max ? String(v.price_max) : '',
      });
      setGroceryItems(v.grocery_items?.length ? v.grocery_items : [{ name: '', unit: 'kg', unit_price: '' }]);
      setGroceryMeta({
        delivery_radius: v.delivery_radius || v.details?.delivery_radius || '',
        delivery_schedule: v.delivery_schedule || v.details?.delivery_schedule || '',
      });
      setDjEquipment(v.dj_equipment?.length ? v.dj_equipment : [{ name: '', unit_price: '' }]);
      setDjPackages(v.dj_packages?.length ? v.dj_packages : [{ name: '', duration_hours: 4, price: '' }]);
      setDjMeta({
        performance_type: v.performance_type || v.details?.performance_type || '',
        genres: Array.isArray(v.genres) ? v.genres.join(', ') : (v.details?.genres || ''),
      });
      setCatererMenu(v.caterer_menu_items?.length ? v.caterer_menu_items : [{ name: '', unit_price: '' }]);
      setCatererMeta({
        cuisine_specializations: Array.isArray(v.cuisine_specializations) ? v.cuisine_specializations.join(', ') : (v.details?.cuisine_specializations || ''),
        dietary_options: Array.isArray(v.dietary_options) ? v.dietary_options.join(', ') : (v.details?.dietary_options || ''),
      });
      setDecorThemes(v.decorator_themes?.length ? v.decorator_themes : [{ name: '', price: '' }]);
      setVenueMeta({
        venue_types: (v.venue_types || []).join(', '),
        amenities: (v.amenities || []).join(', '),
        capacity_min: v.capacity_min ? String(v.capacity_min) : '',
        capacity_max: v.capacity_max ? String(v.capacity_max) : '',
        pricing_model: v.pricing_model || v.details?.pricing_model || '',
        availability_calendar: v.availability_calendar || v.details?.availability_calendar || '',
        cancellation_policy: v.cancellation_policy || v.details?.cancellation_policy || '',
      });
      setMakeupMeta({
        specializations: (v.makeup_specializations || []).join(', '),
        products_used: (v.products_used || []).join(', '),
        travel_charges: v.travel_charges || v.details?.travel_charges || '',
      });
      setMakeupServices(v.makeup_services?.length ? v.makeup_services : [{ name: '', price: '' }]);
      setPhotoMeta({
        photo_services: (v.photo_services || []).join(', '),
        equipment_details: (v.equipment_details || []).join(', '),
        delivery_timeline: v.delivery_timeline || v.details?.delivery_timeline || '',
        raw_footage_policy: v.raw_footage_policy || v.details?.raw_footage_policy || '',
      });
      setPhotoPackages(v.photo_packages?.length ? v.photo_packages : [{ name: '', hours: 8, price: '' }]);
      setTransportMeta({
        vehicle_categories: (v.vehicle_categories || []).join(', '),
        pricing_structure: v.pricing_structure || v.details?.pricing_structure || '',
        insurance_coverage: v.insurance_coverage || v.details?.insurance_coverage || '',
      });
      setTransportVehicles(v.transport_vehicles?.length ? v.transport_vehicles : [{ name: '', capacity: '', price: '' }]);
      setMehandiMeta({
        design_styles: (v.design_styles || []).join(', '),
        quality_type: v.quality_type || v.details?.quality_type || '',
        application_time_estimates: v.application_time_estimates || v.details?.application_time_estimates || '',
      });
      setMehandiServices(v.mehandi_services?.length ? v.mehandi_services : [{ name: '', price: '' }]);
    };
    loadVendor();
  }, [user]);

  const categorySlug = useMemo(() => {
    if (!vendor) return null;
    return CATEGORY_SLUG_MAP[vendor.category_id] || vendor.category_id;
  }, [vendor]);

  useEffect(() => {
    if (!categorySlug) return;
    assistant.getRequirements(categorySlug).then((res) => setRequirements(res.data)).catch(() => setRequirements(null));
  }, [categorySlug]);

  const validate = async () => {
    if (!categorySlug) return;
    const res = await assistant.validateOnboarding({
      category_id: categorySlug,
      business_name: baseForm.business_name,
      owner_name: baseForm.owner_name,
      city: baseForm.city,
      price_min: baseForm.price_min ? Number(baseForm.price_min) : null,
      price_max: baseForm.price_max ? Number(baseForm.price_max) : null,
      grocery_items: groceryItems.filter((i) => i.name),
      delivery_radius: groceryMeta.delivery_radius || null,
      delivery_schedule: groceryMeta.delivery_schedule || null,
      dj_equipment: djEquipment.filter((i) => i.name),
      dj_packages: djPackages.filter((p) => p.name),
      performance_type: djMeta.performance_type || null,
      genres: djMeta.genres ? djMeta.genres.split(',').map((s) => s.trim()).filter(Boolean) : [],
      caterer_menu_items: catererMenu.filter((i) => i.name),
      cuisine_specializations: catererMeta.cuisine_specializations ? catererMeta.cuisine_specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
      dietary_options: catererMeta.dietary_options ? catererMeta.dietary_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
      decorator_themes: decorThemes.filter((i) => i.name),
      venue_types: venueMeta.venue_types ? venueMeta.venue_types.split(',').map((s) => s.trim()).filter(Boolean) : [],
      amenities: venueMeta.amenities ? venueMeta.amenities.split(',').map((s) => s.trim()).filter(Boolean) : [],
      capacity_min: venueMeta.capacity_min ? Number(venueMeta.capacity_min) : null,
      capacity_max: venueMeta.capacity_max ? Number(venueMeta.capacity_max) : null,
      pricing_model: venueMeta.pricing_model || null,
      availability_calendar: venueMeta.availability_calendar || null,
      cancellation_policy: venueMeta.cancellation_policy || null,
      makeup_specializations: makeupMeta.specializations ? makeupMeta.specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
      makeup_services: makeupServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
      products_used: makeupMeta.products_used ? makeupMeta.products_used.split(',').map((s) => s.trim()).filter(Boolean) : [],
      travel_charges: makeupMeta.travel_charges || null,
      photo_services: photoMeta.photo_services ? photoMeta.photo_services.split(',').map((s) => s.trim()).filter(Boolean) : [],
      photo_packages: photoPackages.filter((p) => p.name).map((p) => ({
        ...p,
        hours: Number(p.hours || 0),
        price: Number(p.price || 0),
      })),
      equipment_details: photoMeta.equipment_details ? photoMeta.equipment_details.split(',').map((s) => s.trim()).filter(Boolean) : [],
      delivery_timeline: photoMeta.delivery_timeline || null,
      raw_footage_policy: photoMeta.raw_footage_policy || null,
      transport_vehicles: transportVehicles.filter((v) => v.name).map((v) => ({
        ...v,
        capacity: v.capacity ? Number(v.capacity) : null,
        price: v.price ? Number(v.price) : null,
      })),
      vehicle_categories: transportMeta.vehicle_categories ? transportMeta.vehicle_categories.split(',').map((s) => s.trim()).filter(Boolean) : [],
      pricing_structure: transportMeta.pricing_structure || null,
      insurance_coverage: transportMeta.insurance_coverage || null,
      design_styles: mehandiMeta.design_styles ? mehandiMeta.design_styles.split(',').map((s) => s.trim()).filter(Boolean) : [],
      mehandi_services: mehandiServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
      quality_type: mehandiMeta.quality_type || null,
      application_time_estimates: mehandiMeta.application_time_estimates || null,
    });
    setValidation(res.data);
  };

  useEffect(() => {
    if (vendor) validate();
  }, [vendor, categorySlug]);

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
        dj_equipment: djEquipment.filter((i) => i.name),
        dj_packages: djPackages.filter((p) => p.name).map((p) => ({
          ...p,
          duration_hours: Number(p.duration_hours || 0),
          price: Number(p.price || 0),
        })),
        performance_type: djMeta.performance_type || null,
        genres: djMeta.genres ? djMeta.genres.split(',').map((s) => s.trim()).filter(Boolean) : [],
        caterer_menu_items: catererMenu.filter((i) => i.name).map((i) => ({
          ...i,
          unit_price: Number(i.unit_price || 0),
        })),
        cuisine_specializations: catererMeta.cuisine_specializations ? catererMeta.cuisine_specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
        dietary_options: catererMeta.dietary_options ? catererMeta.dietary_options.split(',').map((s) => s.trim()).filter(Boolean) : [],
        decorator_themes: decorThemes.filter((i) => i.name).map((i) => ({
          ...i,
          price: i.price ? Number(i.price) : null,
        })),
        venue_types: venueMeta.venue_types ? venueMeta.venue_types.split(',').map((s) => s.trim()).filter(Boolean) : [],
        amenities: venueMeta.amenities ? venueMeta.amenities.split(',').map((s) => s.trim()).filter(Boolean) : [],
        capacity_min: venueMeta.capacity_min ? Number(venueMeta.capacity_min) : null,
        capacity_max: venueMeta.capacity_max ? Number(venueMeta.capacity_max) : null,
        pricing_model: venueMeta.pricing_model || null,
        availability_calendar: venueMeta.availability_calendar || null,
        cancellation_policy: venueMeta.cancellation_policy || null,
        makeup_specializations: makeupMeta.specializations ? makeupMeta.specializations.split(',').map((s) => s.trim()).filter(Boolean) : [],
        makeup_services: makeupServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
        products_used: makeupMeta.products_used ? makeupMeta.products_used.split(',').map((s) => s.trim()).filter(Boolean) : [],
        travel_charges: makeupMeta.travel_charges || null,
        photo_services: photoMeta.photo_services ? photoMeta.photo_services.split(',').map((s) => s.trim()).filter(Boolean) : [],
        photo_packages: photoPackages.filter((p) => p.name).map((p) => ({
          ...p,
          hours: Number(p.hours || 0),
          price: Number(p.price || 0),
        })),
        equipment_details: photoMeta.equipment_details ? photoMeta.equipment_details.split(',').map((s) => s.trim()).filter(Boolean) : [],
        delivery_timeline: photoMeta.delivery_timeline || null,
        raw_footage_policy: photoMeta.raw_footage_policy || null,
        transport_vehicles: transportVehicles.filter((v) => v.name).map((v) => ({
          ...v,
          capacity: v.capacity ? Number(v.capacity) : null,
          price: v.price ? Number(v.price) : null,
        })),
        vehicle_categories: transportMeta.vehicle_categories ? transportMeta.vehicle_categories.split(',').map((s) => s.trim()).filter(Boolean) : [],
        pricing_structure: transportMeta.pricing_structure || null,
        insurance_coverage: transportMeta.insurance_coverage || null,
        design_styles: mehandiMeta.design_styles ? mehandiMeta.design_styles.split(',').map((s) => s.trim()).filter(Boolean) : [],
        mehandi_services: mehandiServices.filter((s) => s.name).map((s) => ({ ...s, price: Number(s.price || 0) })),
        quality_type: mehandiMeta.quality_type || null,
        application_time_estimates: mehandiMeta.application_time_estimates || null,
      };
      await vendors.updateOnboarding(vendor.id, payload);
      await validate();
    } finally {
      setSaving(false);
    }
  };

  if (!vendor) {
    return (
      <View style={styles.container}>
        <Paragraph>Loading onboarding...</Paragraph>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Onboarding Completion</Title>
          <Paragraph style={styles.helper}>Finish the details for faster approval.</Paragraph>
          {validation?.missing_required?.length > 0 && (
            <Chip style={styles.chip}>Missing: {validation.missing_required.join(', ')}</Chip>
          )}

          <TextInput label="Business Name" value={baseForm.business_name} onChangeText={(text) => setBaseForm({ ...baseForm, business_name: text })} style={styles.input} />
          <TextInput label="Owner Name" value={baseForm.owner_name} onChangeText={(text) => setBaseForm({ ...baseForm, owner_name: text })} style={styles.input} />
          <TextInput label="City" value={baseForm.city} onChangeText={(text) => setBaseForm({ ...baseForm, city: text })} style={styles.input} />
          <TextInput label="Description" value={baseForm.description} onChangeText={(text) => setBaseForm({ ...baseForm, description: text })} style={styles.input} />

          {categorySlug === 'grocery' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Grocery Items</Title>
              <TextInput label="Delivery Radius" value={groceryMeta.delivery_radius} onChangeText={(text) => setGroceryMeta({ ...groceryMeta, delivery_radius: text })} style={styles.input} />
              <TextInput label="Delivery Schedule" value={groceryMeta.delivery_schedule} onChangeText={(text) => setGroceryMeta({ ...groceryMeta, delivery_schedule: text })} style={styles.input} />
              {groceryItems.map((item, idx) => (
                <View key={`g-${idx}`} style={styles.row}>
                  <TextInput label="Item" value={item.name} onChangeText={(text) => {
                    const next = [...groceryItems];
                    next[idx].name = text;
                    setGroceryItems(next);
                  }} style={styles.input} />
                  <TextInput label="Unit" value={item.unit} onChangeText={(text) => {
                    const next = [...groceryItems];
                    next[idx].unit = text;
                    setGroceryItems(next);
                  }} style={styles.input} />
                  <TextInput label="Price" value={String(item.unit_price || '')} onChangeText={(text) => {
                    const next = [...groceryItems];
                    next[idx].unit_price = text;
                    setGroceryItems(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setGroceryItems([...groceryItems, { name: '', unit: 'kg', unit_price: '' }])}>Add Item</Button>
            </View>
          )}

          {categorySlug === 'entertainment' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>DJ Packages</Title>
              <TextInput label="Performance Type" value={djMeta.performance_type} onChangeText={(text) => setDjMeta({ ...djMeta, performance_type: text })} style={styles.input} />
              <TextInput label="Genres (comma separated)" value={djMeta.genres} onChangeText={(text) => setDjMeta({ ...djMeta, genres: text })} style={styles.input} />
              {djPackages.map((pkg, idx) => (
                <View key={`dj-${idx}`} style={styles.row}>
                  <TextInput label="Package" value={pkg.name} onChangeText={(text) => {
                    const next = [...djPackages];
                    next[idx].name = text;
                    setDjPackages(next);
                  }} style={styles.input} />
                  <TextInput label="Hours" value={String(pkg.duration_hours)} onChangeText={(text) => {
                    const next = [...djPackages];
                    next[idx].duration_hours = text;
                    setDjPackages(next);
                  }} style={styles.input} keyboardType="numeric" />
                  <TextInput label="Price" value={String(pkg.price || '')} onChangeText={(text) => {
                    const next = [...djPackages];
                    next[idx].price = text;
                    setDjPackages(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setDjPackages([...djPackages, { name: '', duration_hours: 4, price: '' }])}>Add Package</Button>
            </View>
          )}

          {categorySlug === 'catering' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Menu Items</Title>
              <TextInput label="Cuisine Specializations" value={catererMeta.cuisine_specializations} onChangeText={(text) => setCatererMeta({ ...catererMeta, cuisine_specializations: text })} style={styles.input} />
              <TextInput label="Dietary Options" value={catererMeta.dietary_options} onChangeText={(text) => setCatererMeta({ ...catererMeta, dietary_options: text })} style={styles.input} />
              {catererMenu.map((item, idx) => (
                <View key={`menu-${idx}`} style={styles.row}>
                  <TextInput label="Item" value={item.name} onChangeText={(text) => {
                    const next = [...catererMenu];
                    next[idx].name = text;
                    setCatererMenu(next);
                  }} style={styles.input} />
                  <TextInput label="Price" value={String(item.unit_price || '')} onChangeText={(text) => {
                    const next = [...catererMenu];
                    next[idx].unit_price = text;
                    setCatererMenu(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setCatererMenu([...catererMenu, { name: '', unit_price: '' }])}>Add Menu Item</Button>
            </View>
          )}

          {categorySlug === 'decor' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Decor Themes</Title>
              {decorThemes.map((item, idx) => (
                <View key={`decor-${idx}`} style={styles.row}>
                  <TextInput label="Theme" value={item.name} onChangeText={(text) => {
                    const next = [...decorThemes];
                    next[idx].name = text;
                    setDecorThemes(next);
                  }} style={styles.input} />
                  <TextInput label="Price" value={String(item.price || '')} onChangeText={(text) => {
                    const next = [...decorThemes];
                    next[idx].price = text;
                    setDecorThemes(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setDecorThemes([...decorThemes, { name: '', price: '' }])}>Add Theme</Button>
            </View>
          )}

          {categorySlug === 'venues' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Venue Details</Title>
              <TextInput label="Venue Types" value={venueMeta.venue_types} onChangeText={(text) => setVenueMeta({ ...venueMeta, venue_types: text })} style={styles.input} />
              <TextInput label="Amenities" value={venueMeta.amenities} onChangeText={(text) => setVenueMeta({ ...venueMeta, amenities: text })} style={styles.input} />
              <TextInput label="Capacity Min" value={venueMeta.capacity_min} onChangeText={(text) => setVenueMeta({ ...venueMeta, capacity_min: text })} style={styles.input} keyboardType="numeric" />
              <TextInput label="Capacity Max" value={venueMeta.capacity_max} onChangeText={(text) => setVenueMeta({ ...venueMeta, capacity_max: text })} style={styles.input} keyboardType="numeric" />
              <TextInput label="Pricing Model" value={venueMeta.pricing_model} onChangeText={(text) => setVenueMeta({ ...venueMeta, pricing_model: text })} style={styles.input} />
              <TextInput label="Availability Calendar" value={venueMeta.availability_calendar} onChangeText={(text) => setVenueMeta({ ...venueMeta, availability_calendar: text })} style={styles.input} />
              <TextInput label="Cancellation Policy" value={venueMeta.cancellation_policy} onChangeText={(text) => setVenueMeta({ ...venueMeta, cancellation_policy: text })} style={styles.input} />
            </View>
          )}

          {categorySlug === 'makeup' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Makeup Services</Title>
              <TextInput label="Specializations" value={makeupMeta.specializations} onChangeText={(text) => setMakeupMeta({ ...makeupMeta, specializations: text })} style={styles.input} />
              <TextInput label="Products Used" value={makeupMeta.products_used} onChangeText={(text) => setMakeupMeta({ ...makeupMeta, products_used: text })} style={styles.input} />
              <TextInput label="Travel Charges" value={makeupMeta.travel_charges} onChangeText={(text) => setMakeupMeta({ ...makeupMeta, travel_charges: text })} style={styles.input} />
              {makeupServices.map((svc, idx) => (
                <View key={`makeup-${idx}`} style={styles.row}>
                  <TextInput label="Service" value={svc.name} onChangeText={(text) => {
                    const next = [...makeupServices];
                    next[idx].name = text;
                    setMakeupServices(next);
                  }} style={styles.input} />
                  <TextInput label="Price" value={String(svc.price || '')} onChangeText={(text) => {
                    const next = [...makeupServices];
                    next[idx].price = text;
                    setMakeupServices(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setMakeupServices([...makeupServices, { name: '', price: '' }])}>Add Service</Button>
            </View>
          )}

          {categorySlug === 'photography' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Photography Packages</Title>
              <TextInput label="Services" value={photoMeta.photo_services} onChangeText={(text) => setPhotoMeta({ ...photoMeta, photo_services: text })} style={styles.input} />
              <TextInput label="Equipment Details" value={photoMeta.equipment_details} onChangeText={(text) => setPhotoMeta({ ...photoMeta, equipment_details: text })} style={styles.input} />
              <TextInput label="Delivery Timeline" value={photoMeta.delivery_timeline} onChangeText={(text) => setPhotoMeta({ ...photoMeta, delivery_timeline: text })} style={styles.input} />
              <TextInput label="Raw Footage Policy" value={photoMeta.raw_footage_policy} onChangeText={(text) => setPhotoMeta({ ...photoMeta, raw_footage_policy: text })} style={styles.input} />
              {photoPackages.map((pkg, idx) => (
                <View key={`photo-${idx}`} style={styles.row}>
                  <TextInput label="Package" value={pkg.name} onChangeText={(text) => {
                    const next = [...photoPackages];
                    next[idx].name = text;
                    setPhotoPackages(next);
                  }} style={styles.input} />
                  <TextInput label="Hours" value={String(pkg.hours || '')} onChangeText={(text) => {
                    const next = [...photoPackages];
                    next[idx].hours = text;
                    setPhotoPackages(next);
                  }} style={styles.input} keyboardType="numeric" />
                  <TextInput label="Price" value={String(pkg.price || '')} onChangeText={(text) => {
                    const next = [...photoPackages];
                    next[idx].price = text;
                    setPhotoPackages(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setPhotoPackages([...photoPackages, { name: '', hours: 8, price: '' }])}>Add Package</Button>
            </View>
          )}

          {categorySlug === 'transport' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Transport Fleet</Title>
              <TextInput label="Vehicle Categories" value={transportMeta.vehicle_categories} onChangeText={(text) => setTransportMeta({ ...transportMeta, vehicle_categories: text })} style={styles.input} />
              <TextInput label="Pricing Structure" value={transportMeta.pricing_structure} onChangeText={(text) => setTransportMeta({ ...transportMeta, pricing_structure: text })} style={styles.input} />
              <TextInput label="Insurance Coverage" value={transportMeta.insurance_coverage} onChangeText={(text) => setTransportMeta({ ...transportMeta, insurance_coverage: text })} style={styles.input} />
              {transportVehicles.map((veh, idx) => (
                <View key={`vehicle-${idx}`} style={styles.row}>
                  <TextInput label="Vehicle" value={veh.name} onChangeText={(text) => {
                    const next = [...transportVehicles];
                    next[idx].name = text;
                    setTransportVehicles(next);
                  }} style={styles.input} />
                  <TextInput label="Capacity" value={String(veh.capacity || '')} onChangeText={(text) => {
                    const next = [...transportVehicles];
                    next[idx].capacity = text;
                    setTransportVehicles(next);
                  }} style={styles.input} keyboardType="numeric" />
                  <TextInput label="Price" value={String(veh.price || '')} onChangeText={(text) => {
                    const next = [...transportVehicles];
                    next[idx].price = text;
                    setTransportVehicles(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setTransportVehicles([...transportVehicles, { name: '', capacity: '', price: '' }])}>Add Vehicle</Button>
            </View>
          )}

          {categorySlug === 'mehandi' && (
            <View style={styles.section}>
              <Title style={styles.sectionTitle}>Mehandi Services</Title>
              <TextInput label="Design Styles" value={mehandiMeta.design_styles} onChangeText={(text) => setMehandiMeta({ ...mehandiMeta, design_styles: text })} style={styles.input} />
              <TextInput label="Quality Type" value={mehandiMeta.quality_type} onChangeText={(text) => setMehandiMeta({ ...mehandiMeta, quality_type: text })} style={styles.input} />
              <TextInput label="Application Time Estimates" value={mehandiMeta.application_time_estimates} onChangeText={(text) => setMehandiMeta({ ...mehandiMeta, application_time_estimates: text })} style={styles.input} />
              {mehandiServices.map((svc, idx) => (
                <View key={`mehandi-${idx}`} style={styles.row}>
                  <TextInput label="Service" value={svc.name} onChangeText={(text) => {
                    const next = [...mehandiServices];
                    next[idx].name = text;
                    setMehandiServices(next);
                  }} style={styles.input} />
                  <TextInput label="Price" value={String(svc.price || '')} onChangeText={(text) => {
                    const next = [...mehandiServices];
                    next[idx].price = text;
                    setMehandiServices(next);
                  }} style={styles.input} keyboardType="numeric" />
                </View>
              ))}
              <Button mode="outlined" onPress={() => setMehandiServices([...mehandiServices, { name: '', price: '' }])}>Add Service</Button>
            </View>
          )}

          <Button mode="contained" onPress={handleSave} loading={saving} style={styles.cta}>
            Save Onboarding
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAF9', padding: 16 },
  card: { paddingVertical: 8 },
  helper: { color: '#78716C', marginBottom: 12 },
  input: { marginBottom: 10 },
  section: { marginTop: 16 },
  sectionTitle: { fontSize: 18, marginBottom: 8 },
  row: { marginBottom: 8 },
  cta: { marginTop: 12 },
  chip: { backgroundColor: '#FEF3C7', marginBottom: 12 },
});

export default VendorOnboardingScreen;
