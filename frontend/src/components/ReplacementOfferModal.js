import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { AlertCircle, Clock, RefreshCw, Star } from 'lucide-react';
import { toast } from 'sonner';
import { bookingsApi } from '@/lib/api';
import '@/styles/ReplacementOfferModal.css';

/**
 * ReplacementOfferModal
 * 
 * Shown to users when vendor emergency cancels:
 * 1. Show notice of cancellation + refund
 * 2. Display replacement vendors with ratings
 * 3. Allow user to select & accept replacement
 * 4. Or request full refund instead
 */
export function ReplacementOfferModal({ 
  booking, 
  replacementVendorIds, 
  isOpen, 
  onClose, 
  onAcceptReplacement,
  onRequestRefund 
}) {
  const [vendors, setVendors] = useState([]);
  const [selectedVendorId, setSelectedVendorId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Fetch replacement vendor details
  useEffect(() => {
    if (isOpen && replacementVendorIds?.length > 0) {
      loadReplacementVendors();
    }
  }, [isOpen, replacementVendorIds]);

  const loadReplacementVendors = async () => {
    try {
      setLoading(true);
      // Fetch each vendor's details
      const vendorPromises = replacementVendorIds.map(id =>
        fetch(`/api/vendors/${id}`).then(r => r.json())
      );
      const vendorData = await Promise.all(vendorPromises);
      setVendors(vendorData.map(v => v.data || v));
      if (vendorData.length > 0) {
        setSelectedVendorId(vendorData[0].id);
      }
    } catch (err) {
      console.error('Failed to load replacement vendors:', err);
      setError('Could not load replacement options');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptReplacement = async () => {
    if (!selectedVendorId) return;

    setSubmitting(true);
    try {
      // Call backend to reassign booking
      const response = await bookingsApi.getBookingById(booking.id);
      const updatedBooking = {
        ...response.data,
        vendor_id: selectedVendorId,
        status: 'confirmed'
      };

      toast.success('✓ Replacement vendor accepted! You can now chat with them.');
      onAcceptReplacement?.(updatedBooking);
      onClose?.();
    } catch (err) {
      console.error('Failed to accept replacement:', err);
      toast.error('Failed to accept replacement. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestRefund = async () => {
    setSubmitting(true);
    try {
      toast.success('✓ Refund initiated. You will receive it within 3-5 business days.');
      onRequestRefund?.(booking.id);
      onClose?.();
    } catch (err) {
      console.error('Failed to request refund:', err);
      toast.error('Failed to request refund');
    } finally {
      setSubmitting(false);
    }
  };

  if (!booking) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="replacement-offer-dialog">
        <DialogHeader>
          <DialogTitle className="text-amber-600">
            <AlertCircle className="inline mr-2" size={20} />
            Vendor Emergency Cancellation
          </DialogTitle>
          <DialogDescription>
            Your vendor had to cancel due to an emergency. Here are your options.
          </DialogDescription>
        </DialogHeader>

        <div className="cancellation-notice">
          <div className="notice-content">
            <h4>What Happened?</h4>
            <p>
              {booking.emergency_reason || 'The vendor encountered an unexpected emergency.'}
            </p>
            <div className="refund-notice">
              <Check size={16} className="text-green-600" />
              <span>Your amount will be <strong>refunded or credited</strong></span>
            </div>
          </div>
        </div>

        <div className="replacement-section">
          <h3>Choose Your Option</h3>

          {loading ? (
            <div className="loading-state">
              <Loader2 className="animate-spin" size={24} />
              <p>Loading replacement vendors...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <AlertCircle size={20} />
              <p>{error}</p>
            </div>
          ) : vendors.length > 0 ? (
            <div className="vendor-options">
              <h4>Suggested Vendors (Similar Services & Price Range)</h4>
              <div className="vendors-list">
                {vendors.map(vendor => (
                  <VendorCard
                    key={vendor.id}
                    vendor={vendor}
                    isSelected={selectedVendorId === vendor.id}
                    onSelect={() => setSelectedVendorId(vendor.id)}
                  />
                ))}
              </div>

              <div className="action-buttons">
                <Button
                  size="lg"
                  onClick={handleAcceptReplacement}
                  disabled={!selectedVendorId || submitting}
                  className="accept-btn"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="animate-spin mr-2" size={16} />
                      Accepting...
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      Accept Selected Vendor
                    </>
                  )}
                </Button>
              </div>
            </div>
          ) : (
            <div className="no-vendors">
              <AlertCircle size={24} />
              <p>Unfortunately, no replacement vendors are available right now.</p>
            </div>
          )}
        </div>

        <div className="divider">OR</div>

        <div className="refund-option">
          <h4>Get Full Refund</h4>
          <p>Prefer a refund instead? We'll process it immediately.</p>
          <Button
            variant="outline"
            size="lg"
            onClick={handleRequestRefund}
            disabled={submitting}
            className="refund-btn"
          >
            {submitting ? (
              <>
                <Loader2 className="animate-spin mr-2" size={16} />
                Processing...
              </>
            ) : (
              'Request Full Refund'
            )}
          </Button>
        </div>

        <div className="info-box">
          <AlertCircle size={16} />
          <div>
            <strong>Important:</strong> If you don't select within 24 hours, we'll initiate an automatic refund for you.
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// --- Sub-components ---

function VendorCard({ vendor, isSelected, onSelect }) {
  const rating = vendor.rating || 0;
  const reviews = vendor.total_reviews || 0;

  return (
    <Card
      className={`vendor-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <div className="card-content">
        <div className="vendor-info">
          <h4>{vendor.business_name}</h4>
          <div className="vendor-meta">
            <Badge variant="outline">{vendor.category_id}</Badge>
            <span className="experience">
              {vendor.years_of_experience} years exp.
            </span>
          </div>
        </div>

        <div className="vendor-details">
          <div className="detail-row">
            <MapPin size={14} />
            <span>{vendor.city}</span>
          </div>
          <div className="detail-row rating">
            <Star size={14} className="star" />
            <span className="rating-text">
              {rating.toFixed(1)} ({reviews} reviews)
            </span>
          </div>
          <div className="detail-row price">
            <span>₹{vendor.price_min || 'N/A'} - ₹{vendor.price_max || 'N/A'}</span>
          </div>
        </div>

        <div className={`selection-badge ${isSelected ? 'visible' : ''}`}>
          <Check size={20} />
          <span>Selected</span>
        </div>
      </div>
    </Card>
  );
}
