import { useCallback, useMemo, useState } from 'react';
import apiClient from '../lib/apiClient';

const SERVICE_CATEGORIES = [
  'photography',
  'catering',
  'decoration',
  'makeup',
  'lighting',
  'videography',
];

const RENTAL_CATEGORIES = ['venue', 'tent_furniture'];
const GROCERY_CATEGORIES = ['grocery'];

function normalizeCategorySlug(value) {
  const raw = String(value || '').trim().toLowerCase().replace(/\s+/g, '_');
  const aliases = {
    decor: 'decoration',
    decorator: 'decoration',
    makeup_artist: 'makeup',
    venue_hall: 'venue',
    wholesale_grocery: 'grocery',
  };
  return aliases[raw] || raw;
}

function getGroupFromCategory(categorySlug) {
  const normalized = normalizeCategorySlug(categorySlug);
  if (SERVICE_CATEGORIES.includes(normalized)) return 'SERVICE';
  if (RENTAL_CATEGORIES.includes(normalized)) return 'RENTAL';
  if (GROCERY_CATEGORIES.includes(normalized)) return 'GROCERY';
  return 'SERVICE';
}

function randomKey(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function messageFromError(err) {
  return err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Request failed';
}

export function useBookingFlow(categorySlug) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('IDLE');
  const [lastResponse, setLastResponse] = useState(null);

  const group = useMemo(() => getGroupFromCategory(categorySlug), [categorySlug]);
  const normalizedCategorySlug = useMemo(() => normalizeCategorySlug(categorySlug), [categorySlug]);

  const config = useMemo(() => {
    if (group === 'SERVICE') {
      return {
        lockTtlMinutes: 30,
        vendorSlaHours: 4,
        supportsVendorAcceptance: true,
        supportsEscrow: true,
      };
    }
    if (group === 'RENTAL') {
      return {
        lockTtlMinutes: 20,
        depositPercent: 30,
        supportsVendorAcceptance: false,
        supportsEscrow: false,
      };
    }
    return {
      lockTtlMinutes: 15,
      autoConfirmAfterPayment: true,
      supportsVendorAcceptance: false,
      supportsEscrow: false,
    };
  }, [group]);

  const createIntent = useCallback(
    async (payload) => {
      setLoading(true);
      setError('');
      try {
        let response;
        if (group === 'SERVICE') {
          response = await apiClient.post('/bookings/service/intent', {
            ...payload,
            category_slug: normalizedCategorySlug,
            idempotency_key: payload?.idempotency_key || randomKey('svc'),
          });
          setStatus('PENDING_VENDOR');
        } else if (group === 'RENTAL') {
          response = await apiClient.post('/bookings/rental/intent', {
            ...payload,
            category_slug: normalizedCategorySlug,
            idempotency_key: payload?.idempotency_key || randomKey('rnt'),
          });
          setStatus('DEPOSIT_PENDING');
        } else {
          response = await apiClient.post('/grocery/cart/reserve', payload);
          setStatus('RESERVED');
        }
        setLastResponse(response);
        return response;
      } catch (err) {
        const msg = messageFromError(err);
        setError(msg);
        setStatus('FAILED');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [group, normalizedCategorySlug],
  );

  const payNow = useCallback(
    async (payload) => {
      setLoading(true);
      setError('');
      try {
        let response;
        if (group === 'SERVICE') {
          if (!payload?.intent_id) {
            throw new Error('intent_id is required for service payment');
          }
          response = await apiClient.post(`/bookings/${payload.intent_id}/pay`);
          setStatus('PAYMENT_CREATED');
        } else if (group === 'RENTAL') {
          if (!payload?.booking_id) {
            throw new Error('booking_id is required for rental balance payment');
          }
          response = await apiClient.post(`/bookings/rental/${payload.booking_id}/pay-balance`, payload || {});
          setStatus('BALANCE_PAYMENT_CREATED');
        } else {
          if (!payload?.lock_id) {
            throw new Error('lock_id is required for grocery checkout');
          }
          response = await apiClient.post('/grocery/checkout', {
            lock_id: payload.lock_id,
            idempotency_key: payload?.idempotency_key || randomKey('gck'),
            delivery_address: payload?.delivery_address,
            notes: payload?.notes,
          });
          setStatus('PAYMENT_CREATED');
        }
        setLastResponse(response);
        return response;
      } catch (err) {
        const msg = messageFromError(err);
        setError(msg);
        setStatus('FAILED');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [group],
  );

  return {
    group,
    config,
    status,
    loading,
    error,
    lastResponse,
    createIntent,
    payNow,
  };
}

export default useBookingFlow;

