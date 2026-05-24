import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Chip, Text, Button } from 'react-native-paper';
import { formatCurrency } from '../utils/formatters';

const STATUS_STEPS = ['pending', 'confirmed', 'paid', 'completed', 'refunded', 'cancelled'];

const OrderDetailScreen = ({ route, navigation }) => {
  const { order } = route.params || {};

  if (!order) {
    return (
      <View style={styles.container}>
        <Card style={styles.card}>
          <Card.Content>
            <Title>Order not found</Title>
            <Paragraph>We couldn’t load this booking.</Paragraph>
          </Card.Content>
        </Card>
      </View>
    );
  }

  const status = (order.status || 'pending').toLowerCase();
  const paymentStatus = (order.payment_status || order.paymentStatus || status).toLowerCase();

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Booking #{order.id?.slice?.(0, 8) || order.id}</Title>
          <Paragraph style={styles.subText}>{order.vendor_name || 'Vendor booking'}</Paragraph>

          <View style={styles.amountRow}>
            <Text style={styles.amount}>{formatCurrency(order.total_amount)}</Text>
            <Chip style={styles.statusChip}>{status}</Chip>
          </View>

          <View style={styles.timeline}>
            {STATUS_STEPS.map((step) => {
              const active = STATUS_STEPS.indexOf(step) <= STATUS_STEPS.indexOf(status);
              return (
                <Chip
                  key={step}
                  mode={active ? 'flat' : 'outlined'}
                  style={styles.timelineChip}
                >
                  {step}
                </Chip>
              );
            })}
          </View>

          <View style={styles.section}>
            <Title style={styles.sectionTitle}>Payment</Title>
            <Paragraph>Status: {paymentStatus}</Paragraph>
            {order.payment_id && <Paragraph>Payment ID: {order.payment_id}</Paragraph>}
            {order.refund_id && <Paragraph>Refund ID: {order.refund_id}</Paragraph>}
          </View>

          <View style={styles.section}>
            <Title style={styles.sectionTitle}>Services</Title>
            {(order.services || []).length === 0 ? (
              <Paragraph>No services listed.</Paragraph>
            ) : (
              order.services.map((service) => (
                <Paragraph key={service}>{service}</Paragraph>
              ))
            )}
          </View>

          <Button mode="outlined" onPress={() => navigation.goBack()} style={styles.cta}>
            Back to Bookings
          </Button>
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
    margin: 16,
  },
  subText: {
    color: '#78716C',
    marginTop: 4,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
  },
  amount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#BE185D',
  },
  statusChip: {
    backgroundColor: '#FEF3C7',
  },
  timeline: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
  },
  timelineChip: {
    backgroundColor: '#F5F5F4',
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 18,
    marginBottom: 6,
  },
  cta: {
    marginTop: 20,
  },
});

export default OrderDetailScreen;
