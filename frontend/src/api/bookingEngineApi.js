import apiClient from '../lib/apiClient';

export const bookingEngineApi = {
  createBookingIntent: (payload) => apiClient.post('/booking-engine/bookings', payload),
  createPaymentOrder: (payload) => apiClient.post('/booking-engine/payments/create-order', payload),
  verifyPayment: (payload) => apiClient.post('/booking-engine/payments/verify', payload),
  getBooking: (bookingId) => apiClient.get(`/booking-engine/bookings/${bookingId}`),
};

export default bookingEngineApi;
