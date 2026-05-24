
import React, { useEffect, useState } from 'react';

import {
  Provider as PaperProvider,
  MD3LightTheme,
} from 'react-native-paper';
import { AuthProvider } from './src/contexts/AuthContext';
import NetInfo from '@react-native-community/netinfo';

import RootNavigator from './src/navigation/RootNavigator';
import OfflineBanner from './src/components/OfflineBanner';

/* ✅ FIXED THEME */
const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#BE185D',
    secondary: '#C9A962',
    tertiary: '#8B5CF6',
    background: '#FAF8F5',
    surface: '#FFFFFF',
    onSurface: '#292524',
  },
};

export default function App() {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsOffline(!(state.isConnected && state.isInternetReachable !== false));
    });
    return () => unsubscribe();
  }, []);

  return (
    <PaperProvider theme={theme}>
      <AuthProvider>
        <OfflineBanner isOffline={isOffline} />
        <RootNavigator />
      </AuthProvider>
    </PaperProvider>
  );
}
