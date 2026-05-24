import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Button, Text } from 'react-native-paper';
import { vendors, orders } from '../../services/api';

const AdminDashboardScreen = ({ navigation }) => {
  const [metrics, setMetrics] = useState({
    vendors: 0,
    bookings: 0,
    refunds: 0,
  });

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const [vendorsRes, ordersRes] = await Promise.all([
        vendors.getAll(),
        orders.getAll(),
      ]);
      const orderList = ordersRes.data || [];
      const refunds = orderList.filter((order) => order.status === 'refunded').length;
      setMetrics({
        vendors: (vendorsRes.data || []).length,
        bookings: orderList.length,
        refunds,
      });
    } catch (error) {
      console.error('Failed to load admin metrics:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Admin Dashboard</Title>
          <Paragraph>Read-only system overview for emergencies and audits.</Paragraph>
          <View style={styles.metricRow}>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics.vendors}</Text>
              <Text style={styles.metricLabel}>Vendors</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics.bookings}</Text>
              <Text style={styles.metricLabel}>Bookings</Text>
            </View>
            <View style={styles.metricCard}>
              <Text style={styles.metricValue}>{metrics.refunds}</Text>
              <Text style={styles.metricLabel}>Refunds</Text>
            </View>
          </View>
          <Button
            mode="contained"
            onPress={() => navigation.navigate('AdminEmergency')}
            style={styles.cta}
          >
            Emergency Handling
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('AdminVendors')}
            style={styles.cta}
          >
            Vendor Oversight
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
    padding: 16,
  },
  card: {
    paddingVertical: 8,
  },
  metricRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
    marginBottom: 10,
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#F5F5F4',
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#BE185D',
  },
  metricLabel: {
    color: '#78716C',
    marginTop: 4,
  },
  cta: {
    marginTop: 12,
  },
});

export default AdminDashboardScreen;
