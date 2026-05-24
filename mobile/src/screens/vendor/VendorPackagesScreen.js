import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, TextInput, Button, Chip } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { packages } from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

const VendorPackagesScreen = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [packageList, setPackageList] = useState([]);
  const [form, setForm] = useState({
    name: '',
    tier: 'basic',
    price: '',
    description: '',
    includes: '',
  });

  useEffect(() => {
    if (user?.vendor_id) {
      loadPackages();
    }
  }, [user]);

  const loadPackages = async () => {
    try {
      const response = await packages.getAll({ vendor_id: user.vendor_id });
      setPackageList(response.data || []);
    } catch (error) {
      console.error('Failed to load packages:', error);
    }
  };

  const handleCreate = async () => {
    if (!user?.vendor_id) return;
    setLoading(true);
    try {
      const payload = {
        vendor_id: user.vendor_id,
        name: form.name,
        tier: form.tier,
        price: Number(form.price),
        description: form.description,
        includes: form.includes
          ? form.includes.split(',').map((item) => item.trim()).filter(Boolean)
          : [],
      };
      await packages.create(payload);
      setForm({ name: '', tier: 'basic', price: '', description: '', includes: '' });
      loadPackages();
    } catch (error) {
      console.error('Failed to create package:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Packages & Pricing</Title>
          <Paragraph style={styles.helper}>
            Create packages to appear in customer selection.
          </Paragraph>

          <TextInput
            label="Package Name"
            value={form.name}
            onChangeText={(text) => setForm({ ...form, name: text })}
            mode="outlined"
            style={styles.input}
          />
          <View style={styles.tierRow}>
            {['basic', 'standard', 'premium'].map((tier) => (
              <Chip
                key={tier}
                mode={form.tier === tier ? 'flat' : 'outlined'}
                onPress={() => setForm({ ...form, tier })}
                style={styles.tierChip}
              >
                {tier.toUpperCase()}
              </Chip>
            ))}
          </View>
          <TextInput
            label="Price (₹)"
            value={form.price}
            onChangeText={(text) => setForm({ ...form, price: text })}
            mode="outlined"
            keyboardType="numeric"
            style={styles.input}
          />
          <TextInput
            label="Description"
            value={form.description}
            onChangeText={(text) => setForm({ ...form, description: text })}
            mode="outlined"
            multiline
            style={styles.input}
          />
          <TextInput
            label="What's included (comma separated)"
            value={form.includes}
            onChangeText={(text) => setForm({ ...form, includes: text })}
            mode="outlined"
            style={styles.input}
          />

          <Button
            mode="contained"
            onPress={handleCreate}
            loading={loading}
            disabled={loading || !form.name || !form.price}
            style={styles.cta}
          >
            Create Package
          </Button>
        </Card.Content>
      </Card>

      <View style={styles.listSection}>
        <Title style={styles.sectionTitle}>Existing Packages</Title>
        {packageList.length === 0 ? (
          <Card style={styles.card}>
            <Card.Content>
              <Paragraph>No packages created yet.</Paragraph>
            </Card.Content>
          </Card>
        ) : (
          packageList.map((pkg) => (
            <Card key={pkg.id} style={styles.card}>
              <Card.Content>
                <View style={styles.packageHeader}>
                  <Title>{pkg.name}</Title>
                  <Chip mode="outlined">{pkg.tier?.toUpperCase()}</Chip>
                </View>
                <Paragraph>{formatCurrency(pkg.price)}</Paragraph>
                {pkg.description ? <Paragraph>{pkg.description}</Paragraph> : null}
              </Card.Content>
            </Card>
          ))
        )}
      </View>
    </ScrollView>
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
    marginBottom: 12,
  },
  helper: {
    color: '#78716C',
    marginTop: 4,
    marginBottom: 12,
  },
  input: {
    marginBottom: 12,
  },
  tierRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  tierChip: {
    backgroundColor: '#F5F5F4',
  },
  cta: {
    marginTop: 8,
  },
  listSection: {
    marginTop: 4,
  },
  sectionTitle: {
    marginBottom: 10,
    fontSize: 20,
  },
  packageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
});

export default VendorPackagesScreen;
