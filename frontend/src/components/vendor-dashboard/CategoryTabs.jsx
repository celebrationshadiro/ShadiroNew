import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Calendar, Music2, Utensils, Camera, Brush, Sparkles } from 'lucide-react';

const SkeletonCard = ({ lines = 3 }) => (
  <Card className="p-5 bg-white rounded-2xl border border-stone-100 animate-pulse">
    <div className="h-4 w-24 bg-stone-200 rounded mb-3" />
    {[...Array(lines)].map((_, i) => (
      <div key={i} className={`h-3 bg-stone-200 rounded ${i === lines - 1 ? 'w-3/5' : 'w-full'} mb-2`} />
    ))}
  </Card>
);

const CategoryEmptyState = ({ icon: Icon, title, description, cta, onCta }) => (
  <Card className="p-6 bg-white rounded-2xl border border-dashed border-stone-200 text-center flex flex-col items-center justify-center min-h-[220px]">
    <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-3">
      <Icon className="text-primary" size={26} />
    </div>
    <p className="text-lg font-semibold text-stone-900 mb-1">{title}</p>
    <p className="text-sm text-stone-600 mb-4 max-w-md">{description}</p>
    <Button className="rounded-full" onClick={onCta}>
      {cta}
    </Button>
  </Card>
);

const listText = (value) => {
  if (Array.isArray(value)) return value.length ? value.join(', ') : 'Not set';
  if (typeof value === 'string' && value.trim()) return value;
  return 'Not set';
};

const VenueTab = ({ vendor, loading, navigate }) => (
  <div className="space-y-4 transition-all duration-200">
    <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2"><Calendar size={18} /> Venue Operations</h2>
    {loading ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
    ) : (
      <>
        {!(vendor.capacity_min || vendor.capacity_max || (vendor.venue_types || vendor.details?.venue_types)?.length || (vendor.amenities || vendor.details?.amenities)?.length || (vendor.pricing_options || []).length) ? (
          <CategoryEmptyState icon={Calendar} title="Venue details needed" description="Add capacity, venue types, amenities, and availability so users can trust your listing." cta="Complete setup" onCta={() => navigate('/vendor-onboarding?section=venues')} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-5 min-h-[140px]">
              <p className="text-sm text-stone-500">Capacity</p>
              <p className="text-xl font-semibold">{(vendor.capacity_min || vendor.details?.capacity_min || '—')} - {(vendor.capacity_max || vendor.details?.capacity_max || '—')} guests</p>
            </Card>
            <Card className="p-5 min-h-[140px]">
              <p className="text-sm text-stone-500">Venue Types</p>
              <p className="text-lg text-stone-800">{listText(vendor.venue_types || vendor.details?.venue_types)}</p>
            </Card>
            <Card className="p-5 min-h-[140px]">
              <p className="text-sm text-stone-500">Amenities</p>
              <p className="text-lg text-stone-800">{listText(vendor.amenities || vendor.details?.amenities)}</p>
            </Card>
            <Card className="p-5 min-h-[140px]">
              <p className="text-sm text-stone-500">Available Dates</p>
              <p className="text-lg text-stone-800">{vendor.details?.availability_calendar || 'Add calendar in onboarding'}</p>
            </Card>
            <Card className="p-5 md:col-span-2 min-h-[140px]">
              <p className="text-sm text-stone-500">Pricing Options</p>
              <div className="mt-2 grid md:grid-cols-2 gap-3">
                {(vendor.pricing_options || []).map((opt) => (
                  <Card key={opt.id || opt.label} className="p-3 border border-stone-100">
                    <p className="font-semibold">{opt.label}</p>
                    <p className="text-sm text-stone-600">{opt.price} / {opt.unit}</p>
                  </Card>
                ))}
                {(vendor.pricing_options || []).length === 0 && <p className="text-stone-500">Add pricing options via onboarding.</p>}
              </div>
            </Card>
          </div>
        )}
      </>
    )}
  </div>
);

const DJTab = ({ vendor, loading, navigate }) => (
  <div className="space-y-4 transition-all duration-200">
    <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2"><Music2 size={18} /> DJ Setup</h2>
    {loading ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><SkeletonCard /><SkeletonCard /></div>
    ) : (
      <>
        {!(vendor.dj_equipment?.length || vendor.dj_crew_size || vendor.details?.dj_setup_time || (vendor.genres || vendor.details?.genres)?.length) ? (
          <CategoryEmptyState icon={Music2} title="Tell us about your setup" description="Add equipment, team size, setup time, and genres so planners can book you confidently." cta="Complete setup" onCta={() => navigate('/vendor-onboarding?section=entertainment')} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Equipment</p><p className="text-lg text-stone-800">{listText((vendor.dj_equipment || []).map((e) => e.name || e))}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Team size</p><p className="text-xl font-semibold">{vendor.dj_crew_size || 'Not set'}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Setup time</p><p className="text-lg text-stone-800">{vendor.details?.dj_setup_time || 'Not set'}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Genres / Performance</p><p className="text-lg text-stone-800">{listText(vendor.genres || vendor.details?.genres)}</p></Card>
          </div>
        )}
      </>
    )}
  </div>
);

const CatererTab = ({ vendor, loading, navigate }) => (
  <div className="space-y-4 transition-all duration-200">
    <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2"><Utensils size={18} /> Caterer Menu</h2>
    {loading ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><SkeletonCard /><SkeletonCard /></div>
    ) : (
      <>
        {!(vendor.caterer_menu_items?.length || vendor.cuisine_specializations?.length || vendor.details?.cuisine_specializations?.length || vendor.caterer_price_per_plate) ? (
          <CategoryEmptyState icon={Utensils} title="Add menu & pricing" description="Share cuisines, dietary options, and per-plate pricing so hosts can decide faster." cta="Complete setup" onCta={() => navigate('/vendor-onboarding?section=catering')} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Cuisine types</p><p className="text-lg text-stone-800">{listText(vendor.cuisine_specializations || vendor.details?.cuisine_specializations)}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Dietary options</p><p className="text-lg text-stone-800">{listText(vendor.dietary_options || vendor.details?.dietary_options)}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Per plate pricing</p><p className="text-xl font-semibold">₹{vendor.caterer_price_per_plate || '—'}</p></Card>
            <Card className="p-5 md:col-span-2 min-h-[140px]">
              <p className="text-sm text-stone-500">Menu items</p>
              <div className="grid md:grid-cols-2 gap-3 mt-2">
                {(vendor.caterer_menu_items || []).slice(0, 6).map((item) => (
                  <Card key={item.id || item.name} className="p-3 border border-stone-100">
                    <p className="font-semibold">{item.name}</p>
                    <p className="text-sm text-stone-600">₹{item.unit_price} · {item.category || 'Item'}</p>
                  </Card>
                ))}
                {(vendor.caterer_menu_items || []).length === 0 && <p className="text-stone-500">Add menu items in onboarding.</p>}
              </div>
            </Card>
          </div>
        )}
      </>
    )}
  </div>
);

const PhotographyTab = ({ vendor, loading, navigate }) => (
  <div className="space-y-4 transition-all duration-200">
    <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2"><Camera size={18} /> Photo & Video Delivery</h2>
    {loading ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><SkeletonCard /><SkeletonCard /></div>
    ) : (
      <>
        {!(vendor.photo_services?.length || vendor.delivery_timeline || vendor.details?.delivery_timeline || vendor.photo_packages?.length) ? (
          <CategoryEmptyState icon={Camera} title="Show your deliverables" description="Add services, delivery timeline, and sample packages so clients understand what they get." cta="Complete setup" onCta={() => navigate('/vendor-onboarding?section=photography')} />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Deliverables</p><p className="text-lg text-stone-800">{listText(vendor.photo_services || vendor.details?.photo_services)}</p></Card>
              <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Delivery timeline</p><p className="text-lg text-stone-800">{vendor.delivery_timeline || vendor.details?.delivery_timeline || 'Not set'}</p></Card>
              <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Raw footage policy</p><p className="text-lg text-stone-800">{vendor.raw_footage_policy || vendor.details?.raw_footage_policy || 'Not set'}</p></Card>
              <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Equipment</p><p className="text-lg text-stone-800">{listText(vendor.equipment_details || vendor.details?.equipment_details)}</p></Card>
            </div>
            <div className="mt-4 grid md:grid-cols-2 gap-3">
              {(vendor.photo_packages || []).slice(0, 4).map((pkg) => (
                <Card key={pkg.id || pkg.name} className="p-4 border border-stone-100 min-h-[140px]">
                  <p className="font-semibold">{pkg.name}</p>
                  <p className="text-sm text-stone-600">{pkg.hours} hrs · ₹{pkg.price}</p>
                  <p className="text-sm text-stone-500">{listText(pkg.deliverables)}</p>
                </Card>
              ))}
              {(vendor.photo_packages || []).length === 0 && (
                <Card className="p-4 border border-dashed border-stone-200 text-stone-500 min-h-[140px]">Add photo/video packages in onboarding.</Card>
              )}
            </div>
          </>
        )}
      </>
    )}
  </div>
);

const DecoratorTab = ({ vendor, loading, navigate }) => (
  <div className="space-y-4 transition-all duration-200">
    <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2"><Brush size={18} /> Decor Themes</h2>
    {loading ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><SkeletonCard /><SkeletonCard /></div>
    ) : (
      <>
        {!(vendor.decorator_themes?.length || vendor.decorator_inventory?.length || vendor.decorator_setup_types?.length) ? (
          <CategoryEmptyState icon={Brush} title="Add themes & inventory" description="Share themes, inventory, and setup styles so planners can visualise your work." cta="Complete setup" onCta={() => navigate('/vendor-onboarding?section=decor')} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Themes</p><p className="text-lg text-stone-800">{listText((vendor.decorator_themes || []).map((t) => t.name || t))}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Inventory</p><p className="text-lg text-stone-800">{listText((vendor.decorator_inventory || []).map((t) => t.name || t))}</p></Card>
            <Card className="p-5 md:col-span-2 min-h-[140px]"><p className="text-sm text-stone-500">Setup types</p><p className="text-lg text-stone-800">{listText((vendor.decorator_setup_types || []).map((t) => t.name || t))}</p></Card>
          </div>
        )}
      </>
    )}
  </div>
);

const MehandiTab = ({ vendor, loading, navigate }) => (
  <div className="space-y-4 transition-all duration-200">
    <h2 className="text-2xl font-semibold mb-1 flex items-center gap-2"><Sparkles size={18} /> Mehandi Details</h2>
    {loading ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"><SkeletonCard /><SkeletonCard /></div>
    ) : (
      <>
        {!(vendor.design_styles?.length || vendor.mehandi_services?.length || vendor.application_time_estimates || vendor.details?.application_time_estimates) ? (
          <CategoryEmptyState icon={Sparkles} title="Add mehandi details" description="Add design styles, time per guest, and services so guests can plan slots." cta="Complete setup" onCta={() => navigate('/vendor-onboarding?section=mehandi')} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Design styles</p><p className="text-lg text-stone-800">{listText(vendor.design_styles || vendor.details?.design_styles)}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Time per guest</p><p className="text-lg text-stone-800">{vendor.application_time_estimates || vendor.details?.application_time_estimates || 'Not set'}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Services</p><p className="text-lg text-stone-800">{listText((vendor.mehandi_services || []).map((s) => s.name || s))}</p></Card>
            <Card className="p-5 min-h-[140px]"><p className="text-sm text-stone-500">Home service</p><p className="text-lg text-stone-800">{(vendor.home_service ?? vendor.details?.home_service) ? 'Available' : 'Not available'}</p></Card>
          </div>
        )}
      </>
    )}
  </div>
);

export { VenueTab, DJTab, CatererTab, PhotographyTab, DecoratorTab, MehandiTab };
