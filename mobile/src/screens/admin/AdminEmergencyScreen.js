import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Chip } from 'react-native-paper';
import { orders } from '../../services/api';

const AdminEmergencyScreen = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const response = await orders.getAll();
      const emergencyOrders = (response.data || []).filter((order) =>
        ['cancelled', 'refunded'].includes((order.status || '').toLowerCase())
      );
      setAlerts(emergencyOrders);
    } catch (error) {
      console.error('Failed to load emergency orders:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Title style={styles.sectionTitle}>Emergency Handling</Title>
      {alerts.length === 0 ? (
        <Card style={styles.card}>
          <Card.Content>
            <Paragraph>No emergency cases right now.</Paragraph>
          </Card.Content>
        </Card>
      ) : (
        alerts.map((order) => (
          <Card key={order.id} style={styles.card}>
            <Card.Content>
              <View style={styles.headerRow}>
                <Title>Order #{order.id.slice(0, 8)}</Title>
                <Chip>{order.status}</Chip>
              </View>
              <Paragraph>Vendor: {order.vendor_name || order.vendor_id}</Paragraph>
              <Paragraph>User: {order.user_id}</Paragraph>
              {order.refund_id && <Paragraph>Refund ID: {order.refund_id}</Paragraph>}
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
});

export default AdminEmergencyScreen;
