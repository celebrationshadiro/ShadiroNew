import apiClient from './apiClient';

const wrap = (p) => (p && typeof p.then === 'function')
  ? p.then((res) => {
    if (res && typeof res === 'object' && Object.prototype.hasOwnProperty.call(res, 'data')) {
      if (res.success === false) return { data: null };
      return { data: res.data };
    }
    return { data: res };
  })
  : Promise.resolve({ data: p });
const unwrap = (res) => {
  if (res && typeof res === 'object' && Object.prototype.hasOwnProperty.call(res, 'data')) {
    if (res.success === false) return null;
    return res.data;
  }
  return res;
};

function withParams(path, params) {
  if (!params) return path;
  const qs = new URLSearchParams(params).toString();
  return `${path}${qs ? `?${qs}` : ''}`;
}

function toPaise(rupeesOrPaise) {
  const n = Number(rupeesOrPaise || 0);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return Math.round(n);
}

function normalizeOrderToIntentPayload(data = {}) {
  const totalPaise =
    toPaise(data.total_amount_paise) ||
    toPaise(data.amount_paise) ||
    Math.round(Number(data.total_amount || data.amount || 0) * 100);

  const selectedItems = Array.isArray(data.selected_items) ? data.selected_items : [];
  const services = Array.isArray(data.services) ? data.services : [];

  let items = selectedItems
    .map((item, idx) => {
      const qty = Number(item.qty || item.quantity || 1) || 1;
      const unitPricePaise =
        toPaise(item.unit_price_paise) ||
        Math.round(Number(item.unit_price || item.unitPrice || 0) * 100);
      const totalPricePaise =
        toPaise(item.total_price_paise) ||
        toPaise(item.total_price) ||
        (unitPricePaise * qty);
      const title = item.name || item.title || `Item ${idx + 1}`;
      return {
        item_id: String(item.item_id || item.id || `item_${idx + 1}`),
        title: String(title),
        qty: Math.max(1, qty),
        unit_price_paise: Math.max(0, unitPricePaise),
        total_price_paise: Math.max(0, totalPricePaise),
        meta: { unit: item.unit || 'item' },
      };
    })
    .filter((i) => i.total_price_paise > 0);

  if (items.length === 0 && services.length > 0) {
    const unit = Math.max(1, Math.floor(totalPaise / services.length));
    items = services.map((service, idx) => ({
      item_id: `service_${idx + 1}`,
      title: String(service || `Service ${idx + 1}`),
      qty: 1,
      unit_price_paise: idx === services.length - 1 ? totalPaise - (unit * (services.length - 1)) : unit,
      total_price_paise: idx === services.length - 1 ? totalPaise - (unit * (services.length - 1)) : unit,
      meta: { unit: 'service' },
    }));
  }

  if (items.length === 0) {
    items = [
      {
        item_id: 'booking_total',
        title: 'Booking Total',
        qty: 1,
        unit_price_paise: totalPaise,
        total_price_paise: totalPaise,
        meta: { unit: 'booking' },
      },
    ];
  }

  const categoryType = String(data.category_type || data.booking_context || 'service').toLowerCase();
  const eventDate = data.event_date || null;
  const eventTime = data.event_time || '00:00';
  const scheduledAt = eventDate ? `${eventDate}T${eventTime}:00+05:30` : null;

  return {
    idempotency_key: String(data.idempotency_key || `intent_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`),
    user_id: String(data.user_id),
    vendor_id: String(data.vendor_id),
    category_type: categoryType === 'grocery' || categoryType === 'rental' ? categoryType : 'service',
    items,
    total_amount_paise: items.reduce((sum, i) => sum + Number(i.total_price_paise || 0), 0),
    scheduled_at: scheduledAt,
    duration_minutes: data.duration_minutes || null,
    notes: data.notes || data.event_location_notes || null,
    meta: {
      ...(data.meta || {}),
      event_id: data.event_id || null,
      package_id: data.package_id || null,
      pricing_mode: data.pricing_mode || null,
      venue_type: data.venue_type || null,
      event_city: data.event_city || null,
      event_location: data.event_location || null,
      event_date: data.event_date || null,
      event_time: data.event_time || null,
      event_location_lat: data.event_location_lat || null,
      event_location_lng: data.event_location_lng || null,
      booking_context: data.booking_context || null,
      services,
    },
  };
}

export const auth = {
  register: (data) => wrap(apiClient.post('/auth/register', data)),
  login: (data) => wrap(apiClient.post('/auth/login', data)),
  refresh: (refresh_token) => wrap(apiClient.post('/auth/refresh', { refresh_token })),
  logout: (refresh_token) => wrap(apiClient.post('/auth/logout', { refresh_token })),
  getMe: () => wrap(apiClient.get('/auth/me')),
};

export const categories = {
  getAll: () => wrap(apiClient.get('/categories')),
};

export const vendors = {
  getAll: (params) => wrap(apiClient.get(withParams('/vendors', params))),
  getById: (id) => wrap(apiClient.get(`/vendors/${id}`)),
  create: (data) => wrap(apiClient.post('/vendors', data)),
  update: (id, data) => wrap(apiClient.put(`/vendors/${id}`, data)),
  updateOnboarding: (id, data) => wrap(apiClient.put(`/vendors/${id}/onboarding`, data)),
  updatePricingRules: (id, rules) => wrap(apiClient.put(`/vendors/${id}/pricing-rules`, rules)),
  addMedia: (id, data) => wrap(apiClient.post(`/vendors/${id}/media`, data)),
  reorderMedia: (id, mediaOrder) => wrap(apiClient.put(`/vendors/${id}/media/reorder`, { media_order: mediaOrder })),
};

export const events = {
  create: (data) => wrap(apiClient.post('/events', data)),
  getAll: () => wrap(apiClient.get('/events')),
  getById: (id) => wrap(apiClient.get(`/events/${id}`)),
};

export const packages = {
  getAll: (params) => wrap(apiClient.get(withParams('/packages', params))),
  getById: (id) => wrap(apiClient.get(`/packages/${id}`)),
  create: (data) => wrap(apiClient.post('/packages', data)),
  update: (id, data) => wrap(apiClient.put(`/packages/${id}`, data)),
};

export const quotes = {
  create: (data) => wrap(apiClient.post('/quotes', data)),
  getAll: (params) => wrap(apiClient.get(withParams('/quotes', params))),
  respond: (id, data) => wrap(apiClient.put(`/quotes/${id}/respond`, data)),
  uploadAttachment: (file) => {
    const form = new FormData();
    form.append('file', file);
    return wrap(apiClient.post('/quotes/attachments', form));
  },
};

export const orders = {
  // Canonical adapter: old order-like payload -> /bookings/intent
  create: (data) => wrap(apiClient.post('/bookings/intent', normalizeOrderToIntentPayload(data))),
  // Read from canonical bookings list for dashboards
  getAll: () => wrap(apiClient.get('/bookings')),
  getById: (id) => wrap(apiClient.get(`/bookings/${id}`)),
};

export const payments = {
  // Canonical booking payment order
  createOrder: (intentId) => wrap(apiClient.post(`/bookings/${intentId}/pay`)),
  // Canonical payment verification
  verify: (data) => wrap(apiClient.post('/bookings/verify', data)),
};

export const reviews = {
  create: (data) => wrap(apiClient.post('/reviews', data)),
  getAll: (params) => wrap(apiClient.get(withParams('/reviews', params))),
};

export const vendorRegister = {
  register: (data) => wrap(apiClient.post('/vendor-register', data)),
};

export const vendorProfile = {
  getMyVendor: () => wrap(apiClient.get('/vendors/me')),
};

export const vendorEarnings = {
  getSummary: () => wrap(apiClient.get('/vendors/me/earnings')),
  getLedger: () => wrap(apiClient.get('/vendors/me/ledger')),
};

export const vendorPayouts = {
  list: () => wrap(apiClient.get('/vendors/me/payouts')),
  request: (amount) => wrap(apiClient.post('/vendors/me/payouts', { amount })),
};

export const chats = {
  create: (userId, vendorId) => wrap(apiClient.post('/chats', { user_id: userId, vendor_id: vendorId })),
  getAll: () => wrap(apiClient.get('/chats')),
  getMessages: (chatId, params) => wrap(apiClient.get(withParams(`/chats/${chatId}/messages`, params))),
  markRead: (chatId) => wrap(apiClient.post(`/chats/${chatId}/messages/read`)),
};

export const bookingsApi = {
  // Generic bookings list/detail
  getVendorBookings: (params) => wrap(apiClient.get(withParams('/bookings', params))),
  getBookingById: (bookingId) => wrap(apiClient.get(`/bookings/${bookingId}`)),
  getTransitions: (bookingId) => wrap(apiClient.get(`/bookings/${bookingId}/transitions`)),

  // Generic canonical vendor actions
  updateBookingStatus: async (bookingId, status) => {
    const map = { confirmed: 'accept', rejected: 'reject', completed: 'complete' };
    const action = map[status] || status;
    const bookingRes = await apiClient.get(`/bookings/${bookingId}`);
    const booking = unwrap(bookingRes);
    const expected_version = Number(booking?.version || 1);
    return wrap(apiClient.post(`/bookings/${bookingId}/action`, { action, expected_version }));
  },
  // Generic canonical cancel
  cancelBooking: async (bookingId, body) => {
    const bookingRes = await apiClient.get(`/bookings/${bookingId}`);
    const booking = unwrap(bookingRes);
    const expected_version = Number(booking?.version || 1);
    const expected_from_status = booking?.status || 'PAYMENT_RECEIVED';
    const reason = body?.reason || 'cancelled';
    return wrap(
      apiClient.post(`/bookings/${bookingId}/cancel`, {
        expected_from_status,
        expected_version,
        reason,
      })
    );
  },

  // Service category flow
  createServiceIntent: (payload) => wrap(apiClient.post('/bookings/service/intent', payload)),
  serviceVendorAction: (bookingId, action, reason) =>
    wrap(apiClient.post(`/bookings/service/${bookingId}/vendor-action`, { action, reason })),
  serviceMarkProgress: (bookingId) =>
    wrap(apiClient.post(`/bookings/service/${bookingId}/mark-progress`)),
  serviceComplete: (bookingId) =>
    wrap(apiClient.post(`/bookings/service/${bookingId}/complete`)),
  serviceCancel: (bookingId, reason) =>
    wrap(apiClient.post(`/bookings/service/${bookingId}/cancel`, { reason })),
  getServicePending: () => wrap(apiClient.get('/bookings/service/vendor/pending')),

  // Rental category flow
  checkRentalAvailability: (itemId, checkIn, checkOut) =>
    wrap(apiClient.get(withParams(`/bookings/rental/availability/${itemId}`, {
      check_in: checkIn,
      check_out: checkOut,
    }))),
  createRentalIntent: (payload) => wrap(apiClient.post('/bookings/rental/intent', payload)),
  payRentalBalance: (bookingId) => wrap(apiClient.post(`/bookings/rental/${bookingId}/pay-balance`, {})),
  rentalCancel: (bookingId, reason) =>
    wrap(apiClient.post(`/bookings/rental/${bookingId}/cancel`, { reason })),

  // Emergency endpoints are not present in canonical backend yet
  getEmergencyBookings: (_params) => {
    console.warn('[API] Emergency bookings endpoint not implemented');
    return Promise.resolve({ data: [] });
  },
  approveEmergencyReplacement: (_bookingId) => {
    console.warn('[API] approveEmergencyReplacement not implemented');
    return Promise.resolve({ data: null });
  },
  initiateRefund: (_bookingId) => {
    console.warn('[API] initiateRefund not implemented');
    return Promise.resolve({ data: null });
  },
  escalateEmergency: (_bookingId, _reason) => {
    console.warn('[API] escalateEmergency not implemented');
    return Promise.resolve({ data: null });
  },
};

export const bookingFlowsApi = {
  getByVendor: (vendorId) => wrap(apiClient.get(`/booking-flows/vendor/${vendorId}`)),
  getByCategory: (categoryId) => wrap(apiClient.get(`/booking-flows/category/${categoryId}`)),
};

export const servicesApi = {
  // Get all service items for a vendor (for booking UI)
  getVendorServiceItems: (vendorId) => wrap(apiClient.get(`/services/vendor/${vendorId}/items`)),
  // Vendor adds a new service item
  addServiceItem: (item) => wrap(apiClient.post('/services/vendor/items/add', item)),
  // Vendor bulk adds multiple items
  bulkAddServiceItems: (items) => wrap(apiClient.post('/services/vendor/bulk-add-items', items)),
  // Vendor updates a service item
  updateServiceItem: (itemId, data) => wrap(apiClient.put(`/services/vendor/items/${itemId}`, data)),
  // Vendor deletes a service item
  deleteServiceItem: (itemId) => wrap(apiClient.del(`/services/vendor/items/${itemId}`)),
  // Get pre-defined template for a category
  getCategoryTemplate: (categoryId) => wrap(apiClient.get(`/services/category-template/${categoryId}`)),
};

export const admin = {
  getAnalytics: async () => {
    const [revenue, bookings] = await Promise.all([
      apiClient.get('/admin/analytics/revenue'),
      apiClient.get('/admin/analytics/bookings'),
    ]);
    return { data: { revenue: unwrap(revenue), bookings: unwrap(bookings) } };
  },
  getPricingInsights: () => wrap(apiClient.get('/admin/analytics/revenue')),
  getUsers: (params) => wrap(apiClient.get(withParams('/admin/users', params))),
  getVendors: (params) => wrap(apiClient.get(withParams('/admin/vendors', params))),
  approveVendor: (vendorId, body) => wrap(apiClient.post(`/admin/vendors/${vendorId}/action`, { action: 'approve', ...body })),
  toggleFeatured: (vendorId, featured) => wrap(apiClient.post(`/admin/vendors/${vendorId}/action`, { action: 'feature', featured })),
  getBookings: (params) => wrap(apiClient.get(withParams('/admin/bookings', params))),
  getPayments: (params) => wrap(apiClient.get(withParams('/admin/payments', params))),
  updateVendorCommission: (vendorId, payload) => wrap(apiClient.put(`/admin/vendors/${vendorId}`, payload)),
  getEarningsByCategory: () => wrap(apiClient.get('/admin/analytics/revenue')),
  getPendingPayouts: () => wrap(apiClient.get(withParams('/admin/payouts', { status: 'PENDING' }))),
  getPayoutRequests: () => wrap(apiClient.get(withParams('/admin/payouts', { status: 'PENDING' }))),
  approvePayout: (payoutId) => wrap(apiClient.post(`/admin/payouts/${payoutId}/action`, { action: 'approve' })),
  rejectPayout: (payoutId, admin_note) => wrap(apiClient.post(`/admin/payouts/${payoutId}/action`, { action: 'reject', reason: admin_note })),
  getPlatformAuditLogs: (params) => wrap(apiClient.get(withParams('/admin/audit-logs', params))),
  getVendorStats: (vendorId) => wrap(apiClient.get(`/admin/vendors/${vendorId}`)),
  refundPayment: (paymentId, reason) => wrap(apiClient.post(`/admin/payments/${paymentId}/refund`, { reason })),
  blockUser: (userId, reason) => wrap(apiClient.post(`/admin/users/${userId}/action`, { action: 'block', reason })),
  activateUser: (userId) => wrap(apiClient.post(`/admin/users/${userId}/action`, { action: 'activate' })),
  getAuditLogs: (params) => wrap(apiClient.get(withParams('/admin/audit-logs', params))),
  getVendorReliabilityReport: (params) => wrap(apiClient.get(withParams('/admin/vendors/reliability-report', params))),
  getEmergencyBookings: (_params) => Promise.resolve({ data: [] }),
  approveEmergencyReplacement: (_bookingId) => Promise.resolve({ data: null }),
  initiateEmergencyRefund: (_bookingId) => Promise.resolve({ data: null }),
  escalateEmergency: (_bookingId, _reason) => Promise.resolve({ data: null }),
};

export const recommendationsApi = {
  // Get recommendations based on event parameters
  getRecommendations: (params) => wrap(apiClient.get(withParams('/recommendations', params))),
  // Get personalized recommendations from booking history
  getPersonalizedRecommendations: (limit = 5) => wrap(apiClient.get(withParams('/recommendations/personalized', { limit }))),
  // Get trending vendors from last 30 days
  getTrendingVendors: (limit = 5) => wrap(apiClient.get(withParams('/recommendations/trending', { limit }))),
};

export const groceryApi = {
  listVendorItems: (vendorId) => wrap(apiClient.get(`/grocery/vendors/${vendorId}/items`)),
  addItem: (item) => wrap(apiClient.post('/grocery/vendor/items', item)),
  updateItem: (itemId, data) => wrap(apiClient.put(`/grocery/vendor/items/${itemId}`, data)),
  deleteItem: (itemId) => wrap(apiClient.del(`/grocery/vendor/items/${itemId}`)),
  reserveCart: (payload) => wrap(apiClient.post('/grocery/cart/reserve', payload)),
  releaseCart: (lockId) => wrap(apiClient.del(`/grocery/cart/reserve/${lockId}`)),
  checkout: (payload) => wrap(apiClient.post('/grocery/checkout', payload)),
  createOrder: (payload) => wrap(apiClient.post('/grocery/checkout', payload)),
  listOrders: (params) => wrap(apiClient.get(withParams('/grocery/orders', params))),
  getOrder: (orderId) => wrap(apiClient.get(`/grocery/orders/${orderId}`)),
  trackOrder: (orderId) => wrap(apiClient.get(`/grocery/orders/${orderId}/track`)),
  updateOrderStatus: (orderId, status) =>
    wrap(apiClient.post(`/grocery/orders/${orderId}/update-status`, { status })),
};

export const pricingApi = {
  preview: (payload) => wrap(apiClient.post('/pricing/preview', payload)),
};

export const automationApi = {
  createSchedule: (payload) => wrap(apiClient.post('/automation/schedules', payload)),
  getQueue: () => wrap(apiClient.get('/automation/queue')),
};

export const vendorVerificationApi = {
  uploadDocument: (file) => {
    const form = new FormData();
    form.append('file', file);
    return wrap(apiClient.post('/vendor/verification/upload', form));
  },
};

export const disputesApi = {
  create: (payload) => wrap(apiClient.post('/disputes', payload)),
  listAdmin: () => wrap(apiClient.get('/disputes/admin')),
  resolveAdmin: (id, payload) => wrap(apiClient.put(`/disputes/admin/${id}/resolve`, payload)),
};

export const assistantApi = {
  message: (payload) => wrap(apiClient.post('/assistant/message', payload)),
  validateOnboarding: (payload) => wrap(apiClient.post('/assistant/onboarding/validate', payload)),
  getRequirements: (categoryId) => wrap(apiClient.get(`/assistant/onboarding/requirements/${categoryId}`)),
  draftQuote: (payload) => wrap(apiClient.post('/assistant/quote/draft', payload)),
  summarizeNegotiation: (payload) => wrap(apiClient.post('/assistant/negotiation/summary', payload)),
  suggestReply: (payload) => wrap(apiClient.post('/assistant/reply/suggest', payload)),
};

export default apiClient;
