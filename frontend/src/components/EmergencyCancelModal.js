import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { AlertCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { bookingsApi } from '@/lib/api';
import '@/styles/EmergencyCancelModal.css';

/**
 * EmergencyCancelModal
 * 
 * Handles vendor emergency cancellation:
 * 1. Show warning and reasons
 * 2. Collect reason from vendor
 * 3. Submit emergency cancel request
 * 4. Show replacement suggestions to user
 */
export function EmergencyCancelModal({ booking, isOpen, onClose, onSuccess }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('confirm'); // 'confirm' | 'success' | 'error'
  const [replacementSuggestions, setReplacementSuggestions] = useState([]);
  const [error, setError] = useState(null);

  if (!booking) return null;

  const handleCancel = async () => {
    if (!reason.trim()) {
      toast.error('Please provide a reason for cancellation');
      return;
    }

    setLoading(true);
    try {
      // Call backend to trigger emergency cancel
      const response = await bookingsApi.cancelBooking(booking.id, { reason });
      
      // Backend returns replacement suggestions
      const suggestions = response.data?.replacement_suggestions || response.data?.suggestions || [];
      setReplacementSuggestions(suggestions);
      setStep('success');
      
      toast.success('Booking cancelled. User will be notified with replacement options.');
      onSuccess?.();
    } catch (err) {
      console.error('Emergency cancel failed:', err);
      setError(err.message || 'Failed to cancel booking');
      setStep('error');
      toast.error('Failed to cancel booking');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setReason('');
    setStep('confirm');
    setReplacementSuggestions([]);
    setError(null);
    onClose?.();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="emergency-cancel-dialog">
        {step === 'confirm' && (
          <>
            <DialogHeader>
              <DialogTitle className="text-red-600">
                <AlertTriangle className="inline mr-2" size={20} />
                Emergency Cancellation
              </DialogTitle>
              <DialogDescription>
                This will cancel the booking and notify the customer. This action affects your reliability rating.
              </DialogDescription>
            </DialogHeader>

            <div className="emergency-warning-box">
              <AlertCircle size={20} />
              <div>
                <h4>What happens next?</h4>
                <ul>
                  <li>✓ Customer is notified immediately</li>
                  <li>✓ Refund is initiated</li>
                  <li>✓ Alternative vendors suggested</li>
                  <li>⚠ Your emergency count increases</li>
                  <li>⚠ Admin review may be triggered</li>
                </ul>
              </div>
            </div>

            <div className="booking-info">
              <h4>Booking Details</h4>
              <div className="info-row">
                <span>Event Date:</span>
                <strong>{booking.event_date}</strong>
              </div>
              <div className="info-row">
                <span>Location:</span>
                <strong>{booking.location}</strong>
              </div>
              <div className="info-row">
                <span>Amount:</span>
                <strong className="text-green-600">₹{booking.total_amount}</strong>
              </div>
            </div>

            <div className="reason-section">
              <label htmlFor="cancel-reason">
                Reason for Cancellation <span className="text-red-600">*</span>
              </label>
              <Textarea
                id="cancel-reason"
                placeholder="Explain the reason for emergency cancellation (e.g., Medical emergency, Equipment failure, Unavoidable legal issue)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={4}
                className="reason-textarea"
                disabled={loading}
              />
              <p className="text-sm text-gray-500">
                This reason will be visible to admin for verification.
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose} disabled={loading}>
                Don't Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={!reason.trim() || loading}
              >
                {loading && <Loader2 className="animate-spin mr-2" size={16} />}
                {loading ? 'Cancelling...' : 'Confirm Emergency Cancel'}
              </Button>
            </DialogFooter>
          </>
        )}

        {step === 'success' && (
          <>
            <DialogHeader>
              <DialogTitle className="text-green-600">✓ Cancellation Processed</DialogTitle>
              <DialogDescription>
                The booking has been cancelled and the customer has been notified.
              </DialogDescription>
            </DialogHeader>

            <div className="success-message">
              <div className="success-icon">✓</div>
              <h3>Cancellation Complete</h3>
              <p>
                The customer has been sent a refund and replacement vendor suggestions.
              </p>
            </div>

            {replacementSuggestions.length > 0 && (
              <div className="replacement-info">
                <h4>Replacement Vendors Suggested</h4>
                <p className="text-sm text-gray-600">
                  {replacementSuggestions.length} alternative vendors have been recommended to the customer.
                </p>
              </div>
            )}

            <div className="important-notice">
              <AlertCircle size={18} />
              <div>
                <strong>Important:</strong> Admin may review this cancellation as part of vendor reliability verification.
              </div>
            </div>

            <DialogFooter>
              <Button onClick={handleClose}>Close</Button>
            </DialogFooter>
          </>
        )}

        {step === 'error' && (
          <>
            <DialogHeader>
              <DialogTitle className="text-red-600">✗ Cancellation Failed</DialogTitle>
            </DialogHeader>

            <div className="error-message">
              <div className="error-icon">✗</div>
              <h3>Unable to Process</h3>
              <p>{error || 'An unexpected error occurred. Please try again.'}</p>
            </div>

            <DialogFooter>
              <Button onClick={() => setStep('confirm')}>Back</Button>
              <Button variant="destructive" onClick={handleClose}>
                Close
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
