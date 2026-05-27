import React, { useEffect, useMemo, useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { servicesApi } from '@/lib/api';
import '@/styles/CategoryServiceSelector.css';

const CATEGORY_ALIASES = {
  catering: 'caterer',
  entertainer: 'dj',
  videographer: 'photographer',
  stylist: 'makeup_artist',
  florist: 'decorator',
  mehandi_artist: 'mehendi_artist',
  mehandi: 'mehendi_artist',
  planner: 'event_planner',
};

const normalizeCategory = (categoryId) => {
  const raw = String(categoryId || '').trim().toLowerCase();
  return CATEGORY_ALIASES[raw] || raw;
};

const DEFAULT_QUICK_DETAILS = {
  guest_count: 100,
  service_style: 'buffet',
  music_preference: 'bollywood',
  power_backup: 'yes',
  coverage_type: 'candid_plus_traditional',
  deliverable_priority: 'album_and_reels',
  slot: 'evening',
  parking_needed: 'yes',
  theme_style: 'floral',
  setup_hours: 4,
  service_mode: 'venue',
  people_count: 1,
  hands_count: 20,
  design_level: 'arabic',
  route_km: 5,
  event_scale: 'mid',
  budget_range: '200000-500000',
};

export function CategoryServiceSelector({ vendorId, categoryId, onSelectionChange, onMetaChange }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [quickDetails, setQuickDetails] = useState(DEFAULT_QUICK_DETAILS);
  const normalizedCategory = useMemo(() => normalizeCategory(categoryId), [categoryId]);

  useEffect(() => {
    const loadItems = async () => {
      try {
        setLoading(true);
        const response = await servicesApi.getVendorServiceItems(vendorId);
        setItems(response.data?.items || []);
      } catch (err) {
        console.error('Failed to load service items:', err);
        setError('Could not load available services. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    if (vendorId) loadItems();
  }, [vendorId]);

  useEffect(() => {
    onMetaChange?.(quickDetails);
  }, [quickDetails, onMetaChange]);

  const handleAddItem = (item) => {
    const existing = selectedItems.find((si) => si.id === item.id);
    if (existing) {
      handleUpdateQuantity(item.id, existing.quantity + 1);
      return;
    }
    const newSelection = [
      ...selectedItems,
      {
        id: item.id,
        name: item.name,
        unit_price: item.unit_price,
        unit: item.unit,
        quantity: 1,
        total_price: item.unit_price,
      },
    ];
    setSelectedItems(newSelection);
    onSelectionChange?.(newSelection);
  };

  const handleUpdateQuantity = (itemId, quantity) => {
    if (quantity < 0) return;
    const updated = selectedItems
      .map((si) => (si.id === itemId
        ? { ...si, quantity: Math.max(0, quantity), total_price: Math.max(0, quantity) * si.unit_price }
        : si))
      .filter((si) => si.quantity > 0);
    setSelectedItems(updated);
    onSelectionChange?.(updated);
  };

  const handleRemoveItem = (itemId) => {
    const updated = selectedItems.filter((si) => si.id !== itemId);
    setSelectedItems(updated);
    onSelectionChange?.(updated);
  };

  const setQuickValue = (key, value) => {
    setQuickDetails((prev) => ({ ...prev, [key]: value }));
  };

  const renderQuickInputBar = () => {
    switch (normalizedCategory) {
      case 'caterer':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Guest Count</label>
              <input
                type="range"
                min="20"
                max="1000"
                step="10"
                value={quickDetails.guest_count}
                onChange={(e) => setQuickValue('guest_count', Number(e.target.value))}
              />
              <span>{quickDetails.guest_count}</span>
            </div>
            <div className="quick-field">
              <label>Service Style</label>
              <select value={quickDetails.service_style} onChange={(e) => setQuickValue('service_style', e.target.value)}>
                <option value="buffet">Buffet</option>
                <option value="plated">Plated</option>
                <option value="live_counter">Live Counter</option>
              </select>
            </div>
          </Card>
        );
      case 'dj':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Music Preference</label>
              <select value={quickDetails.music_preference} onChange={(e) => setQuickValue('music_preference', e.target.value)}>
                <option value="bollywood">Bollywood</option>
                <option value="punjabi">Punjabi</option>
                <option value="bhojpuri">Bhojpuri</option>
                <option value="mix">Mixed</option>
              </select>
            </div>
            <div className="quick-field">
              <label>Power Backup</label>
              <select value={quickDetails.power_backup} onChange={(e) => setQuickValue('power_backup', e.target.value)}>
                <option value="yes">Available</option>
                <option value="no">Not Available</option>
              </select>
            </div>
          </Card>
        );
      case 'photographer':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Coverage Type</label>
              <select value={quickDetails.coverage_type} onChange={(e) => setQuickValue('coverage_type', e.target.value)}>
                <option value="candid_plus_traditional">Candid + Traditional</option>
                <option value="candid_only">Candid Only</option>
                <option value="video_only">Video Only</option>
              </select>
            </div>
            <div className="quick-field">
              <label>Output Priority</label>
              <select
                value={quickDetails.deliverable_priority}
                onChange={(e) => setQuickValue('deliverable_priority', e.target.value)}
              >
                <option value="album_and_reels">Album + Reels</option>
                <option value="reels_fast">Fast Reels</option>
                <option value="raw_delivery">Raw Delivery</option>
              </select>
            </div>
          </Card>
        );
      case 'venue':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Slot</label>
              <select value={quickDetails.slot} onChange={(e) => setQuickValue('slot', e.target.value)}>
                <option value="morning">Morning</option>
                <option value="evening">Evening</option>
                <option value="full_day">Full Day</option>
              </select>
            </div>
            <div className="quick-field">
              <label>Parking Needed</label>
              <select value={quickDetails.parking_needed} onChange={(e) => setQuickValue('parking_needed', e.target.value)}>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
          </Card>
        );
      case 'decorator':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Theme Style</label>
              <select value={quickDetails.theme_style} onChange={(e) => setQuickValue('theme_style', e.target.value)}>
                <option value="floral">Floral</option>
                <option value="minimal">Minimal</option>
                <option value="royal">Royal</option>
              </select>
            </div>
            <div className="quick-field">
              <label>Setup Hours</label>
              <input
                type="number"
                min="1"
                max="24"
                value={quickDetails.setup_hours}
                onChange={(e) => setQuickValue('setup_hours', Number(e.target.value))}
              />
            </div>
          </Card>
        );
      case 'makeup_artist':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Service Mode</label>
              <select value={quickDetails.service_mode} onChange={(e) => setQuickValue('service_mode', e.target.value)}>
                <option value="venue">Venue</option>
                <option value="home">Home Service</option>
              </select>
            </div>
            <div className="quick-field">
              <label>People Count</label>
              <input
                type="number"
                min="1"
                max="20"
                value={quickDetails.people_count}
                onChange={(e) => setQuickValue('people_count', Number(e.target.value))}
              />
            </div>
          </Card>
        );
      case 'mehendi_artist':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Hands Count</label>
              <input
                type="number"
                min="2"
                max="500"
                value={quickDetails.hands_count}
                onChange={(e) => setQuickValue('hands_count', Number(e.target.value))}
              />
            </div>
            <div className="quick-field">
              <label>Design Level</label>
              <select value={quickDetails.design_level} onChange={(e) => setQuickValue('design_level', e.target.value)}>
                <option value="simple">Simple</option>
                <option value="arabic">Arabic</option>
                <option value="bridal_heavy">Bridal Heavy</option>
              </select>
            </div>
          </Card>
        );
      case 'band':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Route Distance (KM)</label>
              <input
                type="number"
                min="1"
                max="50"
                value={quickDetails.route_km}
                onChange={(e) => setQuickValue('route_km', Number(e.target.value))}
              />
            </div>
          </Card>
        );
      case 'event_planner':
        return (
          <Card className="quick-input-bar">
            <div className="quick-field">
              <label>Event Scale</label>
              <select value={quickDetails.event_scale} onChange={(e) => setQuickValue('event_scale', e.target.value)}>
                <option value="small">Small</option>
                <option value="mid">Mid</option>
                <option value="large">Large</option>
              </select>
            </div>
            <div className="quick-field">
              <label>Budget Range</label>
              <select value={quickDetails.budget_range} onChange={(e) => setQuickValue('budget_range', e.target.value)}>
                <option value="50000-200000">50K - 2L</option>
                <option value="200000-500000">2L - 5L</option>
                <option value="500000+">5L+</option>
              </select>
            </div>
          </Card>
        );
      default:
        return null;
    }
  };

  const renderByCategory = () => {
    if (!items || items.length === 0) {
      return (
        <div className="service-selector-empty">
          <AlertCircle size={24} />
          <p>No services available. Please contact the vendor.</p>
        </div>
      );
    }

    switch (normalizedCategory) {
      case 'caterer':
        return renderCatererSelector();
      case 'dj':
        return renderDJSelector();
      case 'photographer':
        return renderPhotographerSelector();
      case 'makeup_artist':
        return renderMakeupSelector();
      case 'decorator':
        return renderDecoratorSelector();
      default:
        return renderGenericSelector();
    }
  };

  const renderCatererSelector = () => (
    <div className="service-selector-container">
      <h3>Select Menu Items</h3>
      {renderQuickInputBar()}
      <div className="service-categories">
        {['appetizers', 'main_course', 'desserts', 'beverages'].map((category) => (
          <div key={category} className="service-category">
            <h4>{category.replace('_', ' ').toUpperCase()}</h4>
            <div className="items-grid">
              {items.filter((item) => item.service_category === category).map((item) => (
                <ServiceItemCard
                  key={item.id}
                  item={item}
                  isSelected={selectedItems.some((si) => si.id === item.id)}
                  selectedQty={selectedItems.find((si) => si.id === item.id)?.quantity || 0}
                  onAdd={() => handleAddItem(item)}
                  onUpdateQty={(qty) => handleUpdateQuantity(item.id, qty)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      {selectedItems.length > 0 && (
        <SelectedItemsSummary items={selectedItems} onRemove={handleRemoveItem} onUpdateQty={handleUpdateQuantity} />
      )}
    </div>
  );

  const renderDJSelector = () => (
    <div className="service-selector-container">
      <h3>Select Equipment & Services</h3>
      {renderQuickInputBar()}
      <div className="equipment-checklist">
        {items.map((item) => (
          <div key={item.id} className="equipment-item">
            <div className="checkbox-wrapper">
              <input
                type="checkbox"
                id={item.id}
                checked={selectedItems.some((si) => si.id === item.id)}
                onChange={(e) => (e.target.checked ? handleAddItem(item) : handleRemoveItem(item.id))}
              />
              <label htmlFor={item.id}>
                <div className="item-info">
                  <span className="item-name">{item.name}</span>
                  <span className="item-price">Rs. {item.unit_price}</span>
                </div>
              </label>
            </div>
          </div>
        ))}
      </div>
      {selectedItems.length > 0 && <SelectedItemsSummary items={selectedItems} onRemove={handleRemoveItem} />}
    </div>
  );

  const renderPhotographerSelector = () => (
    <div className="service-selector-container">
      <h3>Select Package</h3>
      {renderQuickInputBar()}
      <div className="package-selector">
        {items.map((item) => (
          <PackageCard
            key={item.id}
            item={item}
            isSelected={selectedItems.some((si) => si.id === item.id)}
            onSelect={() => {
              const picked = [{ id: item.id, name: item.name, unit_price: item.unit_price, unit: item.unit, quantity: 1, total_price: item.unit_price }];
              setSelectedItems(picked);
              onSelectionChange?.(picked);
            }}
          />
        ))}
      </div>
    </div>
  );

  const renderMakeupSelector = () => (
    <div className="service-selector-container">
      <h3>Select Services</h3>
      {renderQuickInputBar()}
      <div className="service-grid">
        {items.map((item) => (
          <ServiceCard
            key={item.id}
            item={item}
            isSelected={selectedItems.some((si) => si.id === item.id)}
            onSelect={() => handleAddItem(item)}
            onUnselect={() => handleRemoveItem(item.id)}
          />
        ))}
      </div>
      {selectedItems.length > 0 && <SelectedItemsSummary items={selectedItems} onRemove={handleRemoveItem} />}
    </div>
  );

  const renderDecoratorSelector = () => (
    <div className="service-selector-container">
      <h3>Select Decoration Items</h3>
      {renderQuickInputBar()}
      <div className="items-grid">
        {items.map((item) => (
          <ServiceItemCard
            key={item.id}
            item={item}
            isSelected={selectedItems.some((si) => si.id === item.id)}
            selectedQty={selectedItems.find((si) => si.id === item.id)?.quantity || 0}
            onAdd={() => handleAddItem(item)}
            onUpdateQty={(qty) => handleUpdateQuantity(item.id, qty)}
          />
        ))}
      </div>
      {selectedItems.length > 0 && (
        <SelectedItemsSummary items={selectedItems} onRemove={handleRemoveItem} onUpdateQty={handleUpdateQuantity} />
      )}
    </div>
  );

  const renderGenericSelector = () => (
    <div className="service-selector-container">
      <h3>Select Services</h3>
      {renderQuickInputBar()}
      <div className="items-grid">
        {items.map((item) => (
          <ServiceItemCard
            key={item.id}
            item={item}
            isSelected={selectedItems.some((si) => si.id === item.id)}
            selectedQty={selectedItems.find((si) => si.id === item.id)?.quantity || 0}
            onAdd={() => handleAddItem(item)}
            onUpdateQty={(qty) => handleUpdateQuantity(item.id, qty)}
          />
        ))}
      </div>
      {selectedItems.length > 0 && (
        <SelectedItemsSummary items={selectedItems} onRemove={handleRemoveItem} onUpdateQty={handleUpdateQuantity} />
      )}
    </div>
  );

  if (loading) return <div className="service-selector-loading">Loading available services...</div>;
  if (error) return <div className="service-selector-error">{error}</div>;
  return renderByCategory();
}

function ServiceItemCard({ item, isSelected, selectedQty, onAdd, onUpdateQty }) {
  return (
    <Card className="service-item-card">
      <div className="item-content">
        <h4>{item.name}</h4>
        <p className="item-description">{item.description}</p>
        <div className="item-footer">
          <span className="item-price">Rs. {item.unit_price}/{item.unit}</span>
          <Badge variant={item.is_available ? 'default' : 'secondary'}>{item.is_available ? 'Available' : 'N/A'}</Badge>
        </div>
      </div>
      {isSelected ? (
        <div className="quantity-selector">
          <Button variant="outline" size="sm" onClick={() => onUpdateQty(selectedQty - 1)}>-</Button>
          <span className="qty-value">{selectedQty}</span>
          <Button size="sm" onClick={() => onUpdateQty(selectedQty + 1)}>+</Button>
        </div>
      ) : (
        <Button onClick={onAdd} disabled={!item.is_available} size="sm"><Plus size={16} /> Add</Button>
      )}
    </Card>
  );
}

function PackageCard({ item, isSelected, onSelect }) {
  return (
    <Card className={`package-card ${isSelected ? 'selected' : ''}`} onClick={onSelect}>
      <div className="package-content">
        <h4>{item.name}</h4>
        <p className="package-price">Rs. {item.unit_price}</p>
        <p className="package-description">{item.description}</p>
        <Button variant={isSelected ? 'default' : 'outline'} className="w-full">{isSelected ? 'Selected' : 'Select Package'}</Button>
      </div>
    </Card>
  );
}

function ServiceCard({ item, isSelected, onSelect, onUnselect }) {
  return (
    <Card className={`service-card ${isSelected ? 'selected' : ''}`} onClick={() => (isSelected ? onUnselect() : onSelect())}>
      <div className="service-content">
        <h4>{item.name}</h4>
        <p className="service-price">Rs. {item.unit_price}</p>
        <Button variant={isSelected ? 'default' : 'outline'} className="w-full">{isSelected ? 'Selected' : 'Select'}</Button>
      </div>
    </Card>
  );
}

function SelectedItemsSummary({ items, onRemove, onUpdateQty }) {
  const total = items.reduce((sum, item) => sum + item.total_price, 0);
  return (
    <Card className="selected-items-summary">
      <h4>Selected Items ({items.length})</h4>
      <div className="items-list">
        {items.map((item) => (
          <div key={item.id} className="selected-item">
            <div className="item-info-row">
              <span className="item-name">{item.name}</span>
              {item.quantity > 1 && <span className="qty-badge">x{item.quantity}</span>}
              <span className="item-amount">Rs. {item.total_price}</span>
            </div>
            {onUpdateQty && (
              <div className="qty-controls">
                <Button variant="outline" size="xs" onClick={() => onUpdateQty(item.id, item.quantity - 1)}>-</Button>
                <span>{item.quantity}</span>
                <Button variant="outline" size="xs" onClick={() => onUpdateQty(item.id, item.quantity + 1)}>+</Button>
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={() => onRemove(item.id)} className="remove-btn">
              <Trash2 size={16} />
            </Button>
          </div>
        ))}
      </div>
      <div className="summary-total"><strong>Total: Rs. {total.toFixed(2)}</strong></div>
    </Card>
  );
}
