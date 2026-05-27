import apiClient from './apiClient';

function withParams(path, params) {
  if (!params) return path;
  const qs = new URLSearchParams(params).toString();
  return `${path}${qs ? `?${qs}` : ''}`;
}

export const admin = {
  getAnalytics: () => apiClient.get('/admin/analytics'),
  getUsers: (params) => apiClient.get(withParams('/admin/users', params)),
  getVendors: (params) => apiClient.get(withParams('/admin/vendors', params)),
  approveVendor: (vendorId, action, reason) => apiClient.put(`/admin/vendors/${vendorId}/approve`, { action, reason }),
  toggleFeatured: (vendorId, featured) => apiClient.put(withParams(`/admin/vendors/${vendorId}/featured`, { featured })),
  getBookings: (params) => apiClient.get(withParams('/admin/bookings', params)),
  getPayments: (params) => apiClient.get(withParams('/admin/payments', params)),
  updateVendorCommission: (vendorId, payload) => apiClient.put(`/admin/vendors/${vendorId}/commission`, payload),
  getEarningsByCategory: () => apiClient.get('/admin/earnings/categories'),
  getPendingPayouts: () => apiClient.get('/admin/payouts/pending'),
  getPayoutRequests: () => apiClient.get('/admin/payouts/requests'),
  approvePayout: (payoutId) => apiClient.post(`/admin/payouts/${payoutId}/approve`),
  rejectPayout: (payoutId, admin_note) => apiClient.post(`/admin/payouts/${payoutId}/reject`, { admin_note }),
};

export default admin;
