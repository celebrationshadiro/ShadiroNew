import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, TextInput, Button } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { vendors } from '../../services/api';
import AssistantWidget from '../../components/AssistantWidget';

const VendorProfileScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [vendor, setVendor] = useState(null);
  const [profile, setProfile] = useState({
    business_name: '',
    location: '',
    description: '',
    years_experience: '',
    base_price: '',
    phone: '',
  });

  useEffect(() => {
    if (user?.vendor_id) {
      loadProfile();
    }
  }, [user]);

  const loadProfile = async () => {
    try {
      const response = await vendors.getById(user.vendor_id);
      setVendor(response.data);
      setProfile({
        business_name: response.data.business_name || '',
        location: response.data.location || '',
        description: response.data.description || '',
        years_experience: response.data.years_experience?.toString() || '',
        base_price: response.data.base_price?.toString() || '',
        phone: response.data.phone || '',
      });
    } catch (error) {
      console.error('Failed to load vendor profile:', error);
    }
  };

  const handleSave = async () => {
    if (!user?.vendor_id) return;
    setLoading(true);
    try {
      await vendors.update(user.vendor_id, {
        business_name: profile.business_name,
        location: profile.location,
        description: profile.description,
        years_experience: profile.years_experience ? Number(profile.years_experience) : null,
        base_price: profile.base_price ? Number(profile.base_price) : null,
        phone: profile.phone,
      });
    } catch (error) {
      console.error('Failed to update vendor profile:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Vendor Profile</Title>
          <Paragraph style={styles.helper}>
            Update your public business information.
          </Paragraph>

          <TextInput
            label="Business Name"
            value={profile.business_name}
            onChangeText={(text) => setProfile({ ...profile, business_name: text })}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="Location"
            value={profile.location}
            onChangeText={(text) => setProfile({ ...profile, location: text })}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="Description"
            value={profile.description}
            onChangeText={(text) => setProfile({ ...profile, description: text })}
            mode="outlined"
            multiline
            style={styles.input}
          />
          <TextInput
            label="Years of Experience"
            value={profile.years_experience}
            onChangeText={(text) => setProfile({ ...profile, years_experience: text })}
            mode="outlined"
            keyboardType="numeric"
            style={styles.input}
          />
          <TextInput
            label="Base Price (₹)"
            value={profile.base_price}
            onChangeText={(text) => setProfile({ ...profile, base_price: text })}
            mode="outlined"
            keyboardType="numeric"
            style={styles.input}
          />
          <TextInput
            label="Phone"
            value={profile.phone}
            onChangeText={(text) => setProfile({ ...profile, phone: text })}
            mode="outlined"
            keyboardType="phone-pad"
            style={styles.input}
          />

          <Button
            mode="contained"
            onPress={handleSave}
            loading={loading}
            disabled={loading}
            style={styles.cta}
          >
            Save Changes
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
      </ScrollView>
      <AssistantWidget role="vendor" context={{ vendor }} title="Vendor Assistant" />
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
  helper: {
    color: '#78716C',
    marginTop: 4,
    marginBottom: 12,
  },
  input: {
    marginBottom: 12,
  },
  cta: {
    marginTop: 10,
  },
});

export default VendorProfileScreen;
