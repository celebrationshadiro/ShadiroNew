import React, { useState, useEffect } from 'react';
import { View, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { Text, Card, Title, Button, Chip, ActivityIndicator } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { events, orders, quotes } from '../services/api';
import { formatCurrency } from '../utils/formatters';

const DashboardScreen = ({ navigation }) => {
  const { user, logout } = useAuth();
  const [eventList, setEventList] = useState([]);
  const [orderList, setOrderList] = useState([]);
  const [quoteList, setQuoteList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [eventsRes, ordersRes, quotesRes] = await Promise.all([
        events.getAll(),
        orders.getAll(),
        quotes.getAll(),
      ]);
      setEventList(eventsRes.data);
      setOrderList(ordersRes.data);
      setQuoteList(quotesRes.data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigation.navigate('Home');
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#BE185D" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.welcomeText}>Welcome, {user.name}!</Title>
        <Button mode="text" onPress={handleLogout}>Logout</Button>
      </View>

      <View style={styles.statsContainer}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Text style={styles.statNumber}>{eventList.length}</Text>
            <Text style={styles.statLabel}>Events</Text>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Text style={styles.statNumber}>{orderList.length}</Text>
            <Text style={styles.statLabel}>Bookings</Text>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Text style={styles.statNumber}>{quoteList.length}</Text>
            <Text style={styles.statLabel}>Quotes</Text>
          </Card.Content>
        </Card>
      </View>

      <View style={styles.section}>
        <Title style={styles.sectionTitle}>My Events</Title>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('CreateEvent')}
          style={styles.createButton}
          icon="plus"
        >
          Create Event
        </Button>

        {eventList.length === 0 ? (
          <Card style={styles.emptyCard}>
            <Card.Content>
              <Text style={styles.emptyText}>No events yet</Text>
            </Card.Content>
          </Card>
        ) : (
          eventList.map((event) => (
            <Card key={event.id} style={styles.eventCard}>
              <Card.Content>
                <Title>{event.title}</Title>
                <Text>Type: {event.event_type}</Text>
                <Text>Date: {event.date}</Text>
                {event.location && <Text>Location: {event.location}</Text>}
              </Card.Content>
            </Card>
          ))
        )}
      </View>

      <View style={styles.section}>
        <Title style={styles.sectionTitle}>Recent Bookings</Title>
        {orderList.length === 0 ? (
          <Card style={styles.emptyCard}>
            <Card.Content>
              <Text style={styles.emptyText}>No bookings yet</Text>
            </Card.Content>
          </Card>
        ) : (
          orderList.map((order) => (
            <TouchableOpacity
              key={order.id}
              onPress={() => navigation.navigate('OrderDetail', { order })}
            >
              <Card style={styles.orderCard}>
                <Card.Content>
                  <View style={styles.orderHeader}>
                    <Text style={styles.orderId}>Order #{order.id.slice(0, 8)}</Text>
                    <Chip style={styles.statusChip}>{order.status}</Chip>
                  </View>
                  <Text style={styles.orderAmount}>{formatCurrency(order.total_amount)}</Text>
                </Card.Content>
              </Card>
            </TouchableOpacity>
          ))
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: '#BE185D',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  welcomeText: {
    color: '#fff',
    fontSize: 24,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 15,
    gap: 10,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#BE185D',
    textAlign: 'center',
  },
  statLabel: {
    fontSize: 14,
    color: '#78716C',
    textAlign: 'center',
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 22,
    marginBottom: 15,
  },
  createButton: {
    marginBottom: 15,
  },
  emptyCard: {
    backgroundColor: '#F5F5F4',
  },
  emptyText: {
    textAlign: 'center',
    color: '#78716C',
    padding: 20,
  },
  eventCard: {
    marginBottom: 10,
  },
  orderCard: {
    marginBottom: 10,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  orderId: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  statusChip: {
    backgroundColor: '#FEF3C7',
  },
  orderAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#BE185D',
  },
});

export default DashboardScreen;
