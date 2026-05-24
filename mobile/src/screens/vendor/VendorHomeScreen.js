import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Title, Paragraph, Button } from 'react-native-paper';

const VendorHomeScreen = ({ navigation }) => {
  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Vendor Dashboard</Title>
          <Paragraph>Manage your profile, packages, and bookings.</Paragraph>
          <Button
            mode="contained"
            onPress={() => navigation.navigate('VendorProfile')}
            style={styles.cta}
          >
            Edit Profile
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('VendorPackages')}
            style={styles.cta}
          >
            Manage Packages
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('VendorBookings')}
            style={styles.cta}
          >
            View Booking Requests
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('VendorQuotes')}
            style={styles.cta}
          >
            Quote Requests
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('VendorOnboarding')}
            style={styles.cta}
          >
            Complete Onboarding
          </Button>
        </Card.Content>
      </Card>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
    padding: 16,
  },
  card: {
    paddingVertical: 8,
  },
  cta: {
    marginTop: 12,
  },
});

export default VendorHomeScreen;
