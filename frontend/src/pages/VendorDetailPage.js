import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { vendors as vendorsApi, packages as packagesApi, chats, servicesApi, events as eventsApi, quotes as quotesApi, groceryApi } from '../lib/api';
import { Button } from '../components/ui/button';
import { CategoryServiceSelector } from '../components/CategoryServiceSelector';
import { ArrowLeft, Star, MapPin, Package } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useGroceryCart } from '../contexts/GroceryCartContext';
import { isProductVendor } from '../lib/vendorType';
import { Card } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import StockBadge from '../components/grocery/StockBadge';
import { toast } from 'sonner';
import AssistantWidget from '../components/assistant/AssistantWidget';
import PackageCompare from '../components/PackageCompare';

const VendorDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addItem, addBundle, cart } = useGroceryCart();
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedServices, setSelectedServices] = useState([]);
  const [packages, setPackages] = useState([]);
  const [packageTier, setPackageTier] = useState('basic');
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [customItems, setCustomItems] = useState([]);
  const [packagesLoading, setPackagesLoading] = useState(false);
  const [serviceItems, setServiceItems] = useState([]);
  const [selectedAddOns, setSelectedAddOns] = useState([]);
  const [showQuoteModal, setShowQuoteModal] = useState(false);
  const [events, setEvents] = useState([]);
  const [quoteMessage, setQuoteMessage] = useState('');
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [selectedEventIds, setSelectedEventIds] = useState([]);
  const [quoteAttachments, setQuoteAttachments] = useState([]);
  const [uploadingAttachments, setUploadingAttachments] = useState(false);
  const [groceryItems, setGroceryItems] = useState([]);
  const [groceryLoading, setGroceryLoading] = useState(false);

  useEffect(() => {
    const loadVendor = async () => {
      try {
        const res = await vendorsApi.getById(id);
        setVendor(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (id) loadVendor();
  }, [id]);

  useEffect(() => {
    const loadPackages = async () => {
      if (!id) return;
      setPackagesLoading(true);
      try {
        const res = await packagesApi.getAll({ vendor_id: id });
        const nextPackages = Array.isArray(res.data) ? res.data : [];
        setPackages(nextPackages);
        if (nextPackages.length === 0) {
          setPackageTier('custom');
          setSelectedPackage(null);
        }
      } catch (err) {
        console.error('Failed to load packages:', err);
      } finally {
        setPackagesLoading(false);
      }
    };
    loadPackages();
  }, [id]);

  useEffect(() => {
    const loadServices = async () => {
      if (!id) return;
      try {
        const res = await servicesApi.getVendorServiceItems(id);
        setServiceItems(res.data?.items || []);
      } catch (err) {
        setServiceItems([]);
      }
    };
    loadServices();
  }, [id]);

  const toggleAddOn = (itemId) => {
    setSelectedAddOns((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
  };

  useEffect(() => {
    const loadGroceryItems = async () => {
      if (!id || !vendor || !isProductVendor(vendor)) return;
      setGroceryLoading(true);
      try {
        const res = await groceryApi.listVendorItems(id);
        setGroceryItems(res.data?.items || []);
      } catch (err) {
        setGroceryItems([]);
      } finally {
        setGroceryLoading(false);
      }
    };
    loadGroceryItems();
  }, [id, vendor]);

  const openQuoteModal = async () => {
    if (!user) {
      navigate('/auth');
      return;
    }
    setShowQuoteModal(true);
    setSelectedEventIds([]);
    try {
      const res = await eventsApi.getAll();
      setEvents(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      setEvents([]);
    }
  };

  const handleUploadAttachments = async (files) => {
    if (!files || files.length === 0) return;
    setUploadingAttachments(true);
    try {
      const uploads = await Promise.all(Array.from(files).map((file) => quotesApi.uploadAttachment(file)));
      const uploaded = uploads.map((res) => res.data);
      setQuoteAttachments((prev) => [...prev, ...uploaded]);
    } catch (err) {
      toast.error('Failed to upload attachment');
    } finally {
      setUploadingAttachments(false);
    }
  };

  const handleSubmitQuote = async () => {
    if (selectedEventIds.length === 0) {
      toast.error('Please select at least one event');
      return;
    }
    setQuoteLoading(true);
    try {
      await Promise.all(selectedEventIds.map((eventId) => quotesApi.create({
        event_id: eventId,
        vendor_id: vendor.id,
        user_id: user.id,
        requested_services: selectedServices.length > 0 ? selectedServices : customItems.map((i) => i.name),
        message: quoteMessage || null,
        attachments: quoteAttachments,
      })));
      toast.success('Quote request sent');
      setShowQuoteModal(false);
      setQuoteMessage('');
      setSelectedEventIds([]);
      setQuoteAttachments([]);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to request quote');
    } finally {
      setQuoteLoading(false);
    }
  };

  const normalizeTier = (tier) => {
    const normalized = (tier || '').toLowerCase();
    const map = { silver: 'basic', gold: 'standard', platinum: 'premium' };
    return map[normalized] || normalized;
  };

  const packagesByTier = packages.reduce((acc, pkg) => {
    const tier = normalizeTier(pkg.tier);
    acc[tier] = acc[tier] || [];
    acc[tier].push(pkg);
    return acc;
  }, {});
  const hasAnyPackages = packages.length > 0;

  if (loading) return <div className="min-h-screen flex items-center justify-center"><p>Loading...</p></div>;
  if (!vendor) return <div className="min-h-screen flex items-center justify-center"><p>Vendor not found</p></div>;

  if (isProductVendor(vendor)) {
    return (
      <>
        <div className="min-h-screen bg-stone-50">
          <div className="max-w-7xl mx-auto w-full px-4 md:px-8 py-8">
            <Button variant="ghost" onClick={() => navigate(-1)} className="mb-6">
              <ArrowLeft size={18} className="mr-2" /> Back
            </Button>
            <div className="bg-white rounded-2xl p-8 shadow-lg">
              <div className="flex items-start justify-between gap-6 flex-wrap">
                <div>
                  <h1 className="text-4xl font-semibold font-heading mb-2">{vendor.business_name}</h1>
                  {vendor.location && (
                    <div className="flex items-center text-stone-600 mb-2">
                      <MapPin size={18} className="mr-2" />
                      <span>{vendor.location}</span>
                    </div>
                  )}
                  {vendor.description && (
                    <p className="text-stone-600 leading-relaxed max-w-2xl">{vendor.description}</p>
                  )}
                  <div className="mt-4">
                    <Button onClick={() => document.getElementById('grocery-items')?.scrollIntoView({ behavior: 'smooth' })} className="rounded-full bg-primary hover:bg-primary/90">
                      Shop Items
                    </Button>
                  </div>
                </div>
                {cart.items.length > 0 && cart.vendorId === vendor.id && (
                  <Button onClick={() => navigate('/grocery/cart')} className="rounded-full">
                    View Cart ({cart.items.length})
                  </Button>
                )}
              </div>

              <div className="mt-8" id="grocery-items">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Shop Items</h2>
                </div>
                {groceryLoading ? (
                  <div className="p-6 bg-stone-50 rounded-xl text-stone-600">Loading items...</div>
                ) : groceryItems.length === 0 ? (
                  <div className="p-6 bg-stone-50 rounded-xl text-stone-600">No items available yet.</div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {groceryItems.map((item) => {
                        const total = Number(item.total_qty ?? item.stock_qty ?? 0);
                        const reserved = Number(item.reserved_qty ?? 0);
                        const sold = Number(item.sold_qty ?? 0);
                        const availableQty = Math.max(0, total - reserved - sold);
                        const canAdd = Boolean(item.is_available) && availableQty > 0;
                        return (
                      <Card key={item.id} className="p-4 border border-stone-200 rounded-xl flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{item.name}</h3>
                          <p className="text-sm text-stone-500">{item.category || 'Grocery'} / {item.unit}</p>
                          <p className="text-sm text-stone-700 mt-2">INR {item.unit_price}</p>
                          <div className="mt-2">
                            <StockBadge item={item} />
                          </div>
                        </div>
                        <Button
                          onClick={() => addItem(vendor.id, {
                            item_id: item.id,
                            name: item.name,
                            unit_price: item.unit_price,
                            unit: item.unit || 'item',
                          })}
                          disabled={!canAdd}
                        >
                          Add to Cart
                        </Button>
                      </Card>
                        );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        <AssistantWidget role="user" context={{ vendor }} title="Grocery Assistant" />
      </>
    );
  }

  const canBook = vendor.onboarding_status === 'complete' || (vendor.onboarding_missing_required || []).length === 0;

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-7xl mx-auto w-full px-4 md:px-8 py-8">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-6">
          <ArrowLeft size={18} className="mr-2" /> Back
        </Button>

        <div className="bg-white rounded-2xl p-8 shadow-lg">
          <h1 className="text-4xl font-semibold font-heading mb-4">{vendor.business_name}</h1>
          
          {vendor.location && (
            <div className="flex items-center text-stone-600 mb-4">
              <MapPin size={18} className="mr-2" />
              <span>{vendor.location}</span>
            </div>
          )}

          <div className="flex items-center gap-4 mb-6">
            <div className="flex items-center">
              <Star size={20} className="text-secondary fill-secondary mr-1" />
              <span className="font-medium text-xl">{vendor.rating.toFixed(1)}</span>
              <span className="text-stone-500 ml-1">({vendor.total_reviews} reviews)</span>
            </div>
          </div>

          {vendor.description && (
            <p className="text-stone-600 leading-relaxed">{vendor.description}</p>
          )}

          {/* Service Items & Category Data */}
          {(serviceItems.length > 0 || vendor.grocery_items?.length > 0 || vendor.dj_packages?.length > 0 || vendor.caterer_menu_items?.length > 0 || vendor.decorator_themes?.length > 0) && (
            <div className="mt-10 pt-8 border-t border-stone-200">
              <h2 className="text-xl font-semibold mb-4">Services & Items</h2>
              {serviceItems.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {serviceItems.map((item) => (
                    <Card key={item.id} className="p-4 border border-stone-200 rounded-xl">
                      <h3 className="font-semibold">{item.name}</h3>
                      <p className="text-sm text-stone-500">{item.service_category || 'Service item'}</p>
                      <p className="text-sm text-stone-700 mt-2">₹{item.unit_price} / {item.unit || 'item'}</p>
                    </Card>
                  ))}
                </div>
              )}
              {vendor.grocery_items?.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">Grocery Catalog</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {vendor.grocery_items.map((item) => (
                      <Card key={item.id} className="p-4 border border-stone-200 rounded-xl">
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-stone-500">{item.category || 'Item'} • {item.availability}</p>
                        <p className="text-sm text-stone-700 mt-2">₹{item.unit_price} / {item.unit}</p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              {vendor.dj_packages?.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">Performance Packages</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {vendor.dj_packages.map((pkg) => (
                      <Card key={pkg.id} className="p-4 border border-stone-200 rounded-xl">
                        <p className="font-medium">{pkg.name}</p>
                        <p className="text-sm text-stone-500">{pkg.duration_hours} hours</p>
                        <p className="text-sm text-stone-700 mt-2">₹{pkg.price?.toLocaleString()}</p>
                        {pkg.includes?.length > 0 && (
                          <p className="text-xs text-stone-500 mt-2">Includes: {pkg.includes.join(', ')}</p>
                        )}
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              {vendor.caterer_menu_items?.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">Menu Items</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {vendor.caterer_menu_items.map((item) => (
                      <Card key={item.id} className="p-4 border border-stone-200 rounded-xl">
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-stone-500">{item.category}</p>
                        <p className="text-sm text-stone-700 mt-2">₹{item.unit_price}</p>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              {vendor.decorator_themes?.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">Decor Themes</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {vendor.decorator_themes.map((theme) => (
                      <Card key={theme.id} className="p-4 border border-stone-200 rounded-xl">
                        <p className="font-medium">{theme.name}</p>
                        <p className="text-sm text-stone-500">{theme.description}</p>
                        {theme.price && <p className="text-sm text-stone-700 mt-2">₹{theme.price}</p>}
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Packages */}
          {!isProductVendor(vendor) && (
          <div className="mt-10 pt-8 border-t border-stone-200">
            <div className="flex items-center gap-2 mb-4">
              <Package size={20} className="text-primary" />
              <h2 className="text-xl font-semibold">Choose a Package</h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-6">
              {['basic', 'standard', 'premium', 'custom'].map((tier) => (
                <Button
                  key={tier}
                  variant={packageTier === tier ? 'primary' : 'outline'}
                  className="rounded-full"
                  onClick={() => {
                    setPackageTier(tier);
                    setSelectedPackage(null);
                  }}
                >
                  {tier.charAt(0).toUpperCase() + tier.slice(1)}
                </Button>
              ))}
            </div>

            {packageTier !== 'custom' && (
              <>
                {packagesLoading ? (
                  <div className="p-6 bg-stone-50 rounded-xl text-stone-600">Loading packages...</div>
                ) : (packagesByTier[packageTier] || []).length === 0 ? (
                  <div className="p-6 bg-stone-50 rounded-xl text-stone-600">
                    {hasAnyPackages
                      ? `No ${packageTier} packages available. Try another tier or choose Custom.`
                      : 'No predefined packages available for this vendor yet. Choose Custom or Request Quote.'}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(packagesByTier[packageTier] || []).map((pkg) => (
                      <div key={pkg.id} className={`border rounded-xl p-5 bg-white ${selectedPackage?.id === pkg.id ? 'border-primary shadow-lg' : 'border-stone-200'}`}>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-lg font-semibold">{pkg.name}</h3>
                          <span className="text-primary font-semibold">₹{pkg.price?.toLocaleString()}</span>
                        </div>
                        {pkg.description && <p className="text-sm text-stone-600 mb-3">{pkg.description}</p>}
                        {pkg.services_included?.length > 0 && (
                          <ul className="text-sm text-stone-600 space-y-1 mb-4">
                            {pkg.services_included.slice(0, 4).map((s, idx) => (
                              <li key={idx}>• {s}</li>
                            ))}
                          </ul>
                        )}
                        {pkg.items_included?.length > 0 && (
                          <p className="text-xs text-stone-500 mb-4">Items: {pkg.items_included.join(', ')}</p>
                        )}
                        <Button
                          variant={selectedPackage?.id === pkg.id ? 'primary' : 'outline'}
                          className="w-full rounded-lg"
                          onClick={() => setSelectedPackage(pkg)}
                        >
                          {selectedPackage?.id === pkg.id ? 'Selected' : 'Select Package'}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {packageTier === 'custom' && vendor.category_id && (
              <div className="mt-6">
                <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl mb-4 text-sm text-emerald-900">
                  Build a custom package by selecting only what you need. Pricing is calculated from the vendor’s item list.
                </div>
                <CategoryServiceSelector
                  vendorId={vendor.id}
                  categoryId={vendor.category_id}
                  onSelectionChange={(items) => {
                    setCustomItems(items);
                    setSelectedServices(items.map((i) => i.name));
                  }}
                />
              </div>
            )}

            {!packagesLoading && packages.length > 1 && (
              <div className="mt-6">
                <PackageCompare
                  packages={packages}
                  onSelect={(pkg) => setSelectedPackage(pkg)}
                />
              </div>
            )}

            {serviceItems.length > 0 && !isProductVendor(vendor) && (
              <div className="mt-8">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold">Add-ons</h3>
                  <p className="text-xs text-stone-500">Optional extras billed by vendor</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {serviceItems.slice(0, 6).map((item) => (
                    <Card key={item.id} className="p-4 border border-stone-200 rounded-xl">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{item.name}</p>
                          <p className="text-xs text-stone-500">{item.category || 'Add-on'} • {item.unit_price ? `₹${item.unit_price}` : ''}</p>
                        </div>
                        <Button
                          size="sm"
                          variant={selectedAddOns.includes(item.id) ? 'secondary' : 'outline'}
                          className="rounded-full"
                          onClick={() => toggleAddOn(item.id)}
                        >
                          {selectedAddOns.includes(item.id) ? 'Added' : 'Add'}
                        </Button>
                      </div>
                      {item.description && <p className="text-xs text-stone-600 mt-2">{item.description}</p>}
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
          )}

          {isProductVendor(vendor) && vendor.grocery_items?.length > 0 && (
            <div className="mt-10 pt-8 border-t border-stone-200">
              <div className="flex items-center gap-2 mb-4">
                <Package size={20} className="text-primary" />
                <h2 className="text-xl font-semibold">Featured Bundles</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {['Daily Essentials Pack', 'Wedding Bulk Pack', 'Monthly Ration Pack'].map((name, idx) => {
                  const items = vendor.grocery_items.slice(idx * 3, idx * 3 + 5);
                  const total = items.reduce((sum, i) => sum + (i.unit_price || 0), 0);
                  return (
                    <Card key={name} className="p-4 border border-stone-100 rounded-xl bg-white">
                      <p className="text-sm font-semibold text-stone-900 mb-1">{name}</p>
                      <p className="text-lg font-bold text-primary mb-1">₹{total.toLocaleString()}</p>
                      <p className="text-xs text-stone-500 mb-3">{items.length} items • swap or add more in cart</p>
                      <ul className="text-xs text-stone-600 space-y-1 mb-3">
                        {items.map((it) => (
                          <li key={it.id}>• {it.name} ({it.unit || 'unit'})</li>
                        ))}
                      </ul>
                      <div className="flex items-center justify-between gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-full"
                          onClick={() => addBundle(vendor.id, items.map((it) => ({
                            item_id: it.id,
                            name: it.name,
                            unit_price: it.unit_price,
                            unit: it.unit || 'item',
                            qty: 1,
                          })))}
                        >
                          Add bundle
                        </Button>
                        <Button
                          size="sm"
                          className="rounded-full"
                          variant="secondary"
                          onClick={() => {
                            navigate(`/grocery/vendors/${vendor.id}`);
                          }}
                        >
                          Edit items
                        </Button>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          <div className="mt-8">
            <div className="space-y-4">
              <Button
                onClick={() => {
                  openQuoteModal();
                }}
                className="w-full bg-primary hover:bg-primary/90 h-14 rounded-full text-lg font-medium"
                data-testid="request-quote-button"
              >
                Request Quote
              </Button>
              {canBook ? (
                <Button
                  onClick={() => {
                    const state = {
                      selectedServices,
                      selectedPackage,
                      customItems,
                      selectedAddOns,
                      pricingMode: packageTier === 'custom' ? 'custom' : 'package',
                    };
                    const packageParam = selectedPackage?.id ? `&package_id=${selectedPackage.id}` : '';
                    navigate(`/checkout?vendor_id=${vendor.id}${packageParam}`, { state });
                  }}
                  className="w-full bg-secondary hover:bg-secondary/90 h-14 rounded-full text-lg font-medium"
                  data-testid="book-now-button"
                  disabled={packageTier !== 'custom' && !selectedPackage}
                >
                  Book Now
                </Button>
              ) : (
                <div className="p-4 rounded-2xl border border-amber-200 bg-amber-50 text-amber-800 text-sm">
                  Booking is temporarily unavailable while this vendor completes onboarding. You can still request a custom quote.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sticky CTA for mobile */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-stone-200 p-3 flex gap-3 md:hidden">
        <Button
          variant="outline"
          className="flex-1 rounded-full"
          onClick={async () => {
            if (!user) {
              navigate('/auth');
              return;
            }
            try {
              const res = await chats.create(user.id, vendor.id);
              const chatId = res.data?.id;
              if (chatId) navigate(`/chat/${chatId}`);
            } catch (err) {
              console.error('Failed to start chat:', err);
            }
          }}
        >
          Chat
        </Button>
        {canBook && (
          <Button
            className="flex-1 rounded-full bg-primary hover:bg-primary/90"
            onClick={() => {
              const state = {
                selectedServices,
                selectedPackage,
                customItems,
                pricingMode: packageTier === 'custom' ? 'custom' : 'package',
              };
              const packageParam = selectedPackage?.id ? `&package_id=${selectedPackage.id}` : '';
              navigate(`/checkout?vendor_id=${vendor.id}${packageParam}`, { state });
            }}
            disabled={packageTier !== 'custom' && !selectedPackage}
          >
            Book
          </Button>
        )}
      </div>
      {showQuoteModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-lg p-6 bg-white rounded-2xl">
            <h2 className="text-2xl font-semibold mb-4">Request a Quote</h2>
            <div className="space-y-4">
              <div>
                <Label>Select Events</Label>
                <div className="mt-2 max-h-40 overflow-y-auto border border-stone-200 rounded-lg p-3 space-y-2">
                  {events.length === 0 && (
                    <p className="text-sm text-stone-500">No events found. Create one below.</p>
                  )}
                  {events.map((event) => {
                    const id = event.id || event._id;
                    return (
                      <label key={id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={selectedEventIds.includes(id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedEventIds([...selectedEventIds, id]);
                            } else {
                              setSelectedEventIds(selectedEventIds.filter((item) => item !== id));
                            }
                          }}
                        />
                        <span>{event.title} • {event.date}</span>
                      </label>
                    );
                  })}
                </div>
                <Button variant="outline" className="mt-2" onClick={() => navigate('/create-event')}>
                  Create New Event
                </Button>
              </div>
              <div>
                <Label>Message</Label>
                <Textarea
                  value={quoteMessage}
                  onChange={(e) => setQuoteMessage(e.target.value)}
                  placeholder="Share your requirements or questions"
                  rows={4}
                />
              </div>
              <div>
                <Label>Attachments (images or PDFs)</Label>
                <input
                  type="file"
                  className="mt-2"
                  multiple
                  onChange={(e) => handleUploadAttachments(e.target.files)}
                />
                {uploadingAttachments && (
                  <p className="text-xs text-stone-500 mt-2">Uploading...</p>
                )}
                {quoteAttachments.length > 0 && (
                  <div className="mt-2 space-y-1 text-xs text-stone-600">
                    {quoteAttachments.map((file, idx) => (
                      <div key={`${file.url}-${idx}`} className="flex items-center justify-between">
                        <span className="truncate">{file.filename || file.url}</span>
                        <button
                          className="text-rose-600"
                          onClick={() => setQuoteAttachments(quoteAttachments.filter((_, i) => i !== idx))}
                          type="button"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowQuoteModal(false)} className="flex-1">
                  Cancel
                </Button>
                <Button onClick={handleSubmitQuote} disabled={quoteLoading} className="flex-1">
                  {quoteLoading ? 'Sending...' : 'Send Quote Request'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
      <AssistantWidget role="user" context={{ vendor }} title="Event Planning Assistant" />
    </div>
  );
};

export default VendorDetailPage;
