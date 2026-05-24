import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Icon } from 'react-native-paper';

import HomeScreen from '../screens/HomeScreen';
import VendorListScreen from '../screens/VendorListScreen';
import DashboardScreen from '../screens/DashboardScreen';
import ChatListScreen from '../screens/chat/ChatListScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator();

const UserTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          height: 68,
          paddingBottom: 8,
          paddingTop: 8,
          backgroundColor: '#0C0A09',
          borderTopColor: 'rgba(201,169,98,0.25)',
          borderTopWidth: 1,
        },
        tabBarActiveTintColor: '#C9A962',
        tabBarInactiveTintColor: '#A8A29E',
        tabBarLabelStyle: {
          fontSize: 12,
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color }) => <Icon source="home-variant" color={color} size={22} />,
        }}
      />
      <Tab.Screen
        name="Explore"
        component={VendorListScreen}
        options={{
          tabBarIcon: ({ color }) => <Icon source="magnify" color={color} size={22} />,
        }}
      />
      <Tab.Screen
        name="Bookings"
        component={DashboardScreen}
        options={{
          tabBarIcon: ({ color }) => <Icon source="calendar-check" color={color} size={22} />,
        }}
      />
      <Tab.Screen
        name="Chats"
        component={ChatListScreen}
        options={{
          tabBarIcon: ({ color }) => <Icon source="message-text" color={color} size={22} />,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ color }) => <Icon source="account-circle" color={color} size={22} />,
        }}
      />
    </Tab.Navigator>
  );
};

export default UserTabs;
