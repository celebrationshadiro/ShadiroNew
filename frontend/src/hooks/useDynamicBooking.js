import { useCallback, useEffect, useMemo, useState } from 'react';
import apiClient from '../lib/apiClient';
import bookingEngineApi from '../api/bookingEngineApi';

function normalizeCategory(vendor) {
  const vendorType = String(vendor?.vendor_type || '').toLowerCase();
  const categoryId = String(vendor?.category_id || '').toLowerCase();
  const categoryName = String(vendor?.category_name || '').toLowerCase();

  if (vendorType.includes('product') || categoryName.includes('grocery')) return 'grocery';
  if (vendorType.includes('rental') || categoryId.includes('rental') || categoryName.includes('rental')) return 'rental';
  return 'service';
}

function randomIdempotency(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export function useDynamicBooking(vendorId) {
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await apiClient.get(`/vendors/${vendorId}`);
        if (isMounted) setVendor(data);
      } catch (err) {
        if (isMounted) setError(err?.response?.data?.detail || err.message || 'Unable to load vendor');
      } finally {
        if (isMounted) setLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [vendorId]);

  const categoryType = useMemo(() => normalizeCategory(vendor), [vendor]);

  const createIntent = useCallback(async (payload) => {
    return bookingEngineApi.createBookingIntent({
      ...payload,
      vendor_id: vendorId,
      category_type: categoryType,
      idempotency_key: randomIdempotency('book'),
    });
  }, [vendorId, categoryType]);

  const createOrder = useCallback(async (intentId) => {
    return bookingEngineApi.createPaymentOrder({
      intent_id: intentId,
      idempotency_key: randomIdempotency('ord'),
    });
  }, []);

  const verifyPayment = useCallback(async (payload) => {
    return bookingEngineApi.verifyPayment({
      ...payload,
      idempotency_key: randomIdempotency('verify'),
    });
  }, []);

  return {
    vendor,
    categoryType,
    loading,
    error,
    createIntent,
    createOrder,
    verifyPayment,
  };
}

export default useDynamicBooking;
