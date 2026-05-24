import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useTheme } from 'react-native-paper';

import VendorHomeScreen from '../screens/vendor/VendorHomeScreen';
import VendorProfileScreen from '../screens/vendor/VendorProfileScreen';
import VendorPackagesScreen from '../screens/vendor/VendorPackagesScreen';
import VendorBookingsScreen from '../screens/vendor/VendorBookingsScreen';
import VendorOnboardingScreen from '../screens/vendor/VendorOnboardingScreen';
import VendorQuotesScreen from '../screens/vendor/VendorQuotesScreen';
import VendorQuoteRespondScreen from '../screens/vendor/VendorQuoteRespondScreen';

const Stack = createStackNavigator();

const VendorStack = () => {
  const theme = useTheme();

  return (
    <Stack.Navigator
      initialRouteName="VendorHome"
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Stack.Screen name="VendorHome" component={VendorHomeScreen} options={{ title: 'Vendor Dashboard' }} />
      <Stack.Screen name="VendorProfile" component={VendorProfileScreen} options={{ title: 'My Profile' }} />
      <Stack.Screen name="VendorPackages" component={VendorPackagesScreen} options={{ title: 'Packages & Pricing' }} />
      <Stack.Screen name="VendorBookings" component={VendorBookingsScreen} options={{ title: 'Booking Requests' }} />
      <Stack.Screen name="VendorQuotes" component={VendorQuotesScreen} options={{ title: 'Quote Requests' }} />
      <Stack.Screen name="VendorQuoteRespond" component={VendorQuoteRespondScreen} options={{ title: 'Respond to Quote' }} />
      <Stack.Screen name="VendorOnboarding" component={VendorOnboardingScreen} options={{ title: 'Complete Onboarding' }} />
    </Stack.Navigator>
  );
};

export default VendorStack;
