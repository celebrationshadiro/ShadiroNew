import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button } from 'react-native-paper';

const ErrorState = ({ title, message, onRetry }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title || 'Something went wrong'}</Text>
      {message ? <Text style={styles.message}>{message}</Text> : null}
      {onRetry ? (
        <Button mode="contained" onPress={onRetry} style={styles.cta}>
          Try again
        </Button>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  title: {
    fontSize: 16,
    color: '#1F2937',
  },
  message: {
    color: '#6B7280',
    marginTop: 6,
    textAlign: 'center',
  },
  cta: {
    marginTop: 12,
  },
});

export default ErrorState;
