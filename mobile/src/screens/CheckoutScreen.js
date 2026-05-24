import React, { useState } from 'react';
import { View, ScrollView, StyleSheet, Alert } from 'react-native';
import { Text, Card, Title, Button, TextInput, ActivityIndicator } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { orders } from '../services/api';
import { formatCurrency } from '../utils/formatters';

const CheckoutScreen = ({ navigation, route }) => {
  const { vendorId, packageName, services = [], totalAmount = 0, tier } = route.params || {};
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [eventId, setEventId] = useState('');

  const handleCheckout = async () => {
    if (!eventId) {
      Alert.alert('Error', 'Please enter an event ID');
      return;
    }

    setLoading(true);
    try {
      const orderData = {
        user_id: user.id,
        vendor_id: vendorId,
        event_id: eventId,
        total_amount: totalAmount,
        services,
        tier,
      };

      const response = await orders.create(orderData);
      const createdOrder = response?.data || orderData;
      Alert.alert('Success', 'Booking created successfully!', [
        { text: 'Track Booking', onPress: () => navigation.navigate('OrderDetail', { order: createdOrder }) },
      ]);
    } catch (error) {
      console.error('Checkout failed:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Checkout failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.title}>Complete Your Booking</Title>

          <TextInput
            label="Event ID *"
            value={eventId}
            onChangeText={setEventId}
            style={styles.input}
            mode="outlined"
            placeholder="Enter your event ID"
          />

          <Text style={styles.helperText}>
            You can find your event ID in your dashboard under "My Events"
          </Text>

          <View style={styles.summarySection}>
            <Title style={styles.summaryTitle}>Order Summary</Title>
            <View style={styles.summaryRow}>
              <Text>Package</Text>
              <Text style={styles.amount}>{packageName || 'Selected Package'}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text>Services</Text>
              <Text style={styles.amount}>{services.length || 0} items</Text>
            </View>
            <View style={[styles.summaryRow, styles.totalRow]}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalAmount}>{formatCurrency(totalAmount)}</Text>
            </View>
          </View>

          <Button
            mode="contained"
            onPress={handleCheckout}
            loading={loading}
            disabled={loading || !eventId}
            style={styles.checkoutButton}
            icon="credit-card"
          >
            Proceed to Payment
          </Button>

          <Text style={styles.secureText}>🔒 Secure payment powered by Razorpay</Text>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  card: {
    margin: 15,
  },
  title: {
    fontSize: 28,
    marginBottom: 20,
  },
  input: {
    marginBottom: 10,
  },
  helperText: {
    fontSize: 12,
    color: '#78716C',
    marginBottom: 20,
  },
  summarySection: {
    marginVertical: 20,
    padding: 15,
    backgroundColor: '#F5F5F4',
    borderRadius: 8,
  },
  summaryTitle: {
    fontSize: 20,
    marginBottom: 15,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  amount: {
    fontWeight: 'bold',
  },
  totalRow: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#D6D3D1',
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  totalAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#BE185D',
  },
  checkoutButton: {
    marginTop: 20,
    paddingVertical: 8,
  },
  secureText: {
    textAlign: 'center',
    marginTop: 15,
    fontSize: 12,
    color: '#78716C',
  },
});

export default CheckoutScreen;
