import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

// Prefer Expo env for production/mobile parity
const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api';
const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const auth = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const vendorRegister = {
  register: (data) => api.post('/vendor-register', data),
};

export const categories = {
  getAll: () => api.get('/categories'),
};

export const vendors = {
  getAll: (params) => api.get('/vendors', { params }),
  getById: (id) => api.get(`/vendors/${id}`),
  update: (id, data) => api.put(`/vendors/${id}`, data),
  updateOnboarding: (id, data) => api.put(`/vendors/${id}/onboarding`, data),
  create: (data) => api.post('/vendors', data),
};

export const events = {
  create: (data) => api.post('/events', data),
  getAll: () => api.get('/events'),
};

export const packages = {
  getAll: (params) => api.get('/packages', { params }),
  getById: (id) => api.get(`/packages/${id}`),
  create: (data) => api.post('/packages', data),
};

export const quotes = {
  create: (data) => api.post('/quotes', data),
  getAll: (params) => api.get('/quotes', { params }),
  respond: (id, data) => api.put(`/quotes/${id}/respond`, data),
  uploadAttachment: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/quotes/attachments', form, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const orders = {
  create: (data) => {
    const totalPaise =
      Number(data?.total_amount_paise || data?.amount_paise || 0) ||
      Math.round(Number(data?.total_amount || data?.amount || 0) * 100);
    const services = Array.isArray(data?.services) ? data.services : [];
    const items =
      services.length > 0
        ? services.map((service, idx) => {
            const unit = Math.max(1, Math.floor(totalPaise / services.length));
            const value = idx === services.length - 1 ? totalPaise - (unit * (services.length - 1)) : unit;
            return {
              item_id: `service_${idx + 1}`,
              title: String(service || `Service ${idx + 1}`),
              qty: 1,
              unit_price_paise: value,
              total_price_paise: value,
              meta: { unit: 'service' },
            };
          })
        : [
            {
              item_id: 'booking_total',
              title: 'Booking Total',
              qty: 1,
              unit_price_paise: totalPaise,
              total_price_paise: totalPaise,
              meta: { unit: 'booking' },
            },
          ];
    const payload = {
      idempotency_key: `intent_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      user_id: String(data?.user_id),
      vendor_id: String(data?.vendor_id),
      category_type: 'service',
      items,
      total_amount_paise: items.reduce((sum, i) => sum + Number(i.total_price_paise || 0), 0),
      scheduled_at: null,
      duration_minutes: null,
      notes: null,
      meta: {
        event_id: data?.event_id || null,
        package_id: data?.package_id || null,
        tier: data?.tier || null,
        services,
      },
    };
    return api.post('/bookings/intent', payload);
  },
  getAll: (params) => api.get('/bookings', { params }),
};

export const bookings = {
  create: (data) => api.post('/bookings', data),
  getVendorBookings: (params) => api.get('/vendor/bookings', { params }),
  accept: (bookingId) => api.post(`/bookings/${bookingId}/accept`),
  reject: (bookingId, data) => api.post(`/bookings/${bookingId}/reject`, data),
  cancel: (bookingId, data) => api.post(`/bookings/${bookingId}/cancel`, data),
};

export const chats = {
  getAll: () => api.get('/chats'),
  getMessages: (chatId) => api.get(`/chats/${chatId}/messages`),
  sendMessage: (chatId, data) => api.post(`/chats/${chatId}/messages`, data),
};

/** Shadiro Smart Delivery Network — loosely coupled from bookings/vendors. */
export const deliveryNetwork = {
  partnerMe: () => api.get('/delivery-network/partner/me'),
  partnerRegister: (data) => api.post('/delivery-network/partner/register', data),
  setOnline: (is_online) => api.patch('/delivery-network/partner/online', { is_online }),
  setLocation: (lat, lng) => api.patch('/delivery-network/partner/location', { lat, lng }),
  inbox: () => api.get('/delivery-network/partner/inbox'),
  accept: (jobId) => api.post(`/delivery-network/partner/jobs/${jobId}/accept`),
  reject: (jobId) => api.post(`/delivery-network/partner/jobs/${jobId}/reject`),
  scanQr: (jobId, body) => api.post(`/delivery-network/partner/jobs/${jobId}/scan-qr`, body),
  transition: (jobId, state) => api.post(`/delivery-network/partner/jobs/${jobId}/transition`, { state }),
  track: (jobId, body) => api.post(`/delivery-network/partner/jobs/${jobId}/track`, body),
};

export const assistant = {
  message: (data) => api.post('/assistant/message', data),
  validateOnboarding: (data) => api.post('/assistant/onboarding/validate', data),
  getRequirements: (categoryId) => api.get(`/assistant/onboarding/requirements/${categoryId}`),
  draftQuote: (data) => api.post('/assistant/quote/draft', data),
  summarizeNegotiation: (data) => api.post('/assistant/negotiation/summary', data),
  suggestReply: (data) => api.post('/assistant/reply/suggest', data),
};

export default api;
