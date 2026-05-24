import React from 'react';
import { View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { ActivityIndicator, useTheme } from 'react-native-paper';

import { useAuth } from '../contexts/AuthContext';
import AuthScreen from '../screens/AuthScreen';
import VendorDetailScreen from '../screens/VendorDetailScreen';
import ChatScreen from '../screens/ChatScreen';
import CheckoutScreen from '../screens/CheckoutScreen';
import CreateEventScreen from '../screens/CreateEventScreen';
import PackageSelectionScreen from '../screens/PackageSelectionScreen';
import OrderDetailScreen from '../screens/OrderDetailScreen';
import UserTabs from './UserTabs';
import VendorStack from './VendorStack';
import DeliveryPartnerDashboardScreen from '../screens/delivery/DeliveryPartnerDashboardScreen';

const RootNavigator = () => {
  const { loading, role } = useAuth();
  const theme = useTheme();

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  if (role === 'vendor') {
    return (
      <NavigationContainer>
        <VendorStack />
      </NavigationContainer>
    );
  }

  if (role === 'admin') {
    return (
      <NavigationContainer>
        <AdminStack />
      </NavigationContainer>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Tabs"
        screenOptions={{
          headerStyle: { backgroundColor: theme.colors.primary },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      >
        <Stack.Screen name="Tabs" component={UserTabs} options={{ headerShown: false }} />
        <Stack.Screen name="Auth" component={AuthScreen} options={{ title: 'Login / Register' }} />
        <Stack.Screen name="VendorDetail" component={VendorDetailScreen} options={{ title: 'Vendor Details' }} />
        <Stack.Screen name="PackageSelection" component={PackageSelectionScreen} options={{ title: 'Select Package' }} />
        <Stack.Screen name="Chat" component={ChatScreen} options={{ title: 'Chat' }} />
        <Stack.Screen name="Checkout" component={CheckoutScreen} options={{ title: 'Checkout' }} />
        <Stack.Screen name="CreateEvent" component={CreateEventScreen} options={{ title: 'Create Event' }} />
        <Stack.Screen name="OrderDetail" component={OrderDetailScreen} options={{ title: 'Booking Status' }} />
        <Stack.Screen
          name="DeliveryPartnerDashboard"
          component={DeliveryPartnerDashboardScreen}
          options={{ title: 'Delivery Hub', headerStyle: { backgroundColor: '#0C0A09' }, headerTintColor: '#C9A962' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FAFAF9',
  },
});

export default RootNavigator;
