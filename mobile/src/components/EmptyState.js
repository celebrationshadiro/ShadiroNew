import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button } from 'react-native-paper';

const EmptyState = ({ title, message, actionLabel, onAction }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title || 'No data found'}</Text>
      {message ? <Text style={styles.message}>{message}</Text> : null}
      {actionLabel && onAction ? (
        <Button mode="outlined" onPress={onAction} style={styles.cta}>
          {actionLabel}
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

export default EmptyState;
