import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button } from 'react-native-paper';

const OfflineBanner = ({ isOffline, onRetry }) => {
  if (!isOffline) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.text}>You are offline. Some features may not work.</Text>
      {onRetry ? (
        <Button mode="outlined" onPress={onRetry} compact style={styles.cta}>
          Retry
        </Button>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  text: {
    color: '#92400E',
    fontSize: 12,
    flex: 1,
    marginRight: 10,
  },
  cta: {
    borderColor: '#92400E',
  },
});

export default OfflineBanner;
