import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { vendorProfile } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

const FIELD_SECTION_MAP = {
  delivery_radius: 'grocery',
  delivery_schedule: 'grocery',
  product_catalog: 'grocery',
  quality_grade: 'grocery',
  minimum_order_quantity: 'grocery',
  venue_name: 'venues',
  venue_types: 'venues',
  amenities: 'venues',
  capacity_min: 'venues',
  capacity_max: 'venues',
  pricing_model: 'venues',
  pricing_options: 'venues',
  availability_calendar: 'venues',
  cancellation_policy: 'venues',
  floor_plans: 'venues',
  photo_gallery: 'venues',
  virtual_tour: 'venues',
  specializations: 'makeup',
  service_menu: 'makeup',
  pricing: 'makeup',
  products_used: 'makeup',
  travel_charges: 'makeup',
  trial_availability: 'makeup',
  before_after_gallery: 'makeup',
  services: 'photography',
  packages: 'photography',
  delivery_timeline: 'photography',
  equipment_details: 'photography',
  raw_footage_policy: 'photography',
  fleet_details: 'transport',
  vehicle_categories: 'transport',
  pricing_structure: 'transport',
  insurance_coverage: 'transport',
  rental_duration_options: 'transport',
  driver_included: 'transport',
  decoration_services: 'transport',
  design_styles: 'mehandi',
  quality_type: 'mehandi',
  application_time_estimates: 'mehandi',
  home_service: 'mehandi',
  themes: 'decor',
  decorator_themes: 'decor',
  decorator_inventory: 'decor',
  decorator_setup_types: 'decor',
  cuisine_specializations: 'catering',
  menu_items: 'catering',
  caterer_menu_items: 'catering',
  dietary_options: 'catering',
  performance_type: 'entertainment',
  genres: 'entertainment',
  dj_packages: 'entertainment',
  dj_equipment: 'entertainment',
};

const VendorOnboardingBanner = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [vendor, setVendor] = useState(null);

  useEffect(() => {
    if (!user || user.role !== 'vendor') return;
    const loadVendor = async () => {
      try {
        const res = await vendorProfile.getMyVendor();
        setVendor(res.data);
      } catch (error) {
        setVendor(null);
      }
    };
    loadVendor();
  }, [user, location.pathname]);

  const missingRequired = useMemo(
    () => vendor?.onboarding_missing_required || [],
    [vendor]
  );
  const shouldShow = vendor && vendor.onboarding_status !== 'complete' && missingRequired.length > 0;

  const primarySection = useMemo(() => {
    for (const field of missingRequired) {
      if (FIELD_SECTION_MAP[field]) return FIELD_SECTION_MAP[field];
    }
    return 'core';
  }, [missingRequired]);

  if (!shouldShow) return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-amber-800">Onboarding Required</p>
          <p className="text-sm text-amber-700">
            Your profile is missing required details: {missingRequired.slice(0, 3).join(', ')}{missingRequired.length > 3 ? '…' : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="px-4 py-2 rounded-full bg-amber-600 text-white text-sm"
            onClick={() => navigate(`/vendor-onboarding?section=${primarySection}`)}
          >
            Complete Onboarding
          </button>
          <button
            className="px-4 py-2 rounded-full border border-amber-200 text-amber-700 text-sm"
            onClick={() => navigate('/vendor-dashboard')}
          >
            View Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default VendorOnboardingBanner;
