import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Chip, Button, TextInput } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { bookings } from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

const VendorBookingsScreen = () => {
  const { user } = useAuth();
  const [bookingList, setBookingList] = useState([]);
  const [rejectingId, setRejectingId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [cancellingId, setCancellingId] = useState(null);
  const [cancellationReason, setCancellationReason] = useState('');
  const [refundMethod, setRefundMethod] = useState('original_payment_method');
  const [statusFilter, setStatusFilter] = useState('pending');

  useEffect(() => {
    loadBookings();
  }, [user, statusFilter]);

  const loadBookings = async () => {
    try {
      const response = await bookings.getVendorBookings({ status: statusFilter, limit: 20 });
      setBookingList(response.data?.bookings || []);
    } catch (error) {
      console.error('Failed to load bookings:', error);
    }
  };

  const handleAccept = async (bookingId) => {
    try {
      await bookings.accept(bookingId);
      loadBookings();
    } catch (error) {
      console.error('Failed to accept booking:', error);
    }
  };

  const handleReject = async (bookingId) => {
    try {
      await bookings.reject(bookingId, { rejection_reason: rejectionReason || 'Unavailable' });
      setRejectingId(null);
      setRejectionReason('');
      loadBookings();
    } catch (error) {
      console.error('Failed to reject booking:', error);
    }
  };

  const handleCancel = async (bookingId) => {
    try {
      await bookings.cancel(bookingId, {
        cancellation_reason: cancellationReason || 'Emergency cancellation',
        refund_method: refundMethod,
      });
      setCancellingId(null);
      setCancellationReason('');
      loadBookings();
    } catch (error) {
      console.error('Failed to cancel booking:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Title style={styles.sectionTitle}>Booking Requests</Title>
      <View style={styles.filterRow}>
        {['pending', 'confirmed', 'completed', 'cancelled', 'rejected'].map((status) => (
          <Chip
            key={status}
            mode={statusFilter === status ? 'flat' : 'outlined'}
            onPress={() => setStatusFilter(status)}
            style={styles.filterChip}
          >
            {status}
          </Chip>
        ))}
      </View>
      {bookingList.length === 0 ? (
        <Card style={styles.card}>
          <Card.Content>
            <Paragraph>No booking requests yet.</Paragraph>
          </Card.Content>
        </Card>
      ) : (
        bookingList.map((booking) => (
          <Card key={booking.id} style={styles.card}>
            <Card.Content>
              <View style={styles.headerRow}>
                <Title>Booking #{booking.booking_id || booking.id.slice(0, 8)}</Title>
                <Chip>{booking.status}</Chip>
              </View>
              <Paragraph>{formatCurrency(booking.total_amount)}</Paragraph>
              <Paragraph>Date: {booking.event_date || '—'}</Paragraph>
              <Paragraph>Location: {booking.location || '—'}</Paragraph>
              <View style={styles.actionRow}>
                {booking.status === 'pending' && (
                  <>
                    <Button mode="contained" onPress={() => handleAccept(booking.booking_id || booking.id)}>
                      Accept
                    </Button>
                    <Button
                      mode="outlined"
                      onPress={() => setRejectingId(booking.booking_id || booking.id)}
                    >
                      Decline
                    </Button>
                  </>
                )}
                {booking.status === 'confirmed' && (
                  <Button
                    mode="outlined"
                    onPress={() => setCancellingId(booking.booking_id || booking.id)}
                  >
                    Cancel Booking
                  </Button>
                )}
              </View>
              {rejectingId === (booking.booking_id || booking.id) && (
                <View style={styles.rejectBox}>
                  <TextInput
                    label="Rejection reason"
                    value={rejectionReason}
                    onChangeText={setRejectionReason}
                    mode="outlined"
                    style={styles.rejectInput}
                  />
                  <Button
                    mode="contained"
                    onPress={() => handleReject(booking.booking_id || booking.id)}
                  >
                    Confirm Rejection
                  </Button>
                </View>
              )}
              {cancellingId === (booking.booking_id || booking.id) && (
                <View style={styles.rejectBox}>
                  <TextInput
                    label="Cancellation reason"
                    value={cancellationReason}
                    onChangeText={setCancellationReason}
                    mode="outlined"
                    style={styles.rejectInput}
                  />
                  <View style={styles.refundRow}>
                    {['original_payment_method', 'wallet_credit'].map((method) => (
                      <Chip
                        key={method}
                        mode={refundMethod === method ? 'flat' : 'outlined'}
                        onPress={() => setRefundMethod(method)}
                        style={styles.filterChip}
                      >
                        {method === 'original_payment_method' ? 'Original Method' : 'Wallet Credit'}
                      </Chip>
                    ))}
                  </View>
                  <Button
                    mode="contained"
                    onPress={() => handleCancel(booking.booking_id || booking.id)}
                  >
                    Confirm Cancellation
                  </Button>
                </View>
              )}
            </Card.Content>
          </Card>
        ))
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
    padding: 16,
  },
  card: {
    paddingVertical: 8,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    marginBottom: 10,
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  filterChip: {
    backgroundColor: '#F5F5F4',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  rejectBox: {
    marginTop: 12,
  },
  rejectInput: {
    marginBottom: 8,
  },
  refundRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
    flexWrap: 'wrap',
  },
});

export default VendorBookingsScreen;
