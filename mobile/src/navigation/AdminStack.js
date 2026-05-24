import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useTheme } from 'react-native-paper';

import AdminDashboardScreen from '../screens/admin/AdminDashboardScreen';
import AdminEmergencyScreen from '../screens/admin/AdminEmergencyScreen';
import AdminVendorsScreen from '../screens/admin/AdminVendorsScreen';

const Stack = createStackNavigator();

const AdminStack = () => {
  const theme = useTheme();

  return (
    <Stack.Navigator
      initialRouteName="AdminDashboard"
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Stack.Screen name="AdminDashboard" component={AdminDashboardScreen} options={{ title: 'Admin Dashboard' }} />
      <Stack.Screen name="AdminEmergency" component={AdminEmergencyScreen} options={{ title: 'Emergency Handling' }} />
      <Stack.Screen name="AdminVendors" component={AdminVendorsScreen} options={{ title: 'Vendor Oversight' }} />
    </Stack.Navigator>
  );
};

export default AdminStack;
