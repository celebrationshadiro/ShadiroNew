import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { ActivityIndicator } from 'react-native-paper';
import { Image as ExpoImage } from 'expo-image';

const LazyImage = ({ source, style }) => {
  const [loading, setLoading] = useState(true);

  return (
    <View style={[styles.container, style]}>
      <ExpoImage
        source={source}
        style={[StyleSheet.absoluteFill, style]}
        contentFit="cover"
        cachePolicy="disk"
        transition={150}
        onLoadStart={() => setLoading(true)}
        onLoadEnd={() => setLoading(false)}
      />
      {loading ? (
        <View style={styles.loader}>
          <ActivityIndicator size="small" color="#BE185D" />
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F5F5F4',
    overflow: 'hidden',
  },
  loader: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default LazyImage;
