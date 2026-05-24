import React, { useMemo, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Chip, Button, Checkbox, Text } from 'react-native-paper';
import { formatCurrency } from '../utils/formatters';

const PackageSelectionScreen = ({ navigation, route }) => {
  const { vendor, packages = [] } = route.params || {};
  const tiers = ['basic', 'standard', 'premium', 'custom'];
  const availableTiers = useMemo(() => {
    const pkgTiers = packages.map((pkg) => pkg.tier?.toLowerCase()).filter(Boolean);
    return [...new Set([...pkgTiers, 'custom'])];
  }, [packages]);
  const [activeTier, setActiveTier] = useState(availableTiers[0] || 'custom');
  const [selectedPackageId, setSelectedPackageId] = useState(null);
  const [customItems, setCustomItems] = useState({});

  const tierPackages = packages.filter(
    (pkg) => (pkg.tier || '').toLowerCase() === activeTier
  );

  const availableItems =
    vendor?.items ||
    vendor?.services ||
    vendor?.service_items || [
      { id: 'item_1', name: 'Venue decoration', price: 5000 },
      { id: 'item_2', name: 'Photography', price: 8000 },
      { id: 'item_3', name: 'Catering', price: 12000 },
    ];

  const selectedCustomItems = availableItems.filter((item) => customItems[item.id]);
  const customTotal = selectedCustomItems.reduce((sum, item) => sum + (item.price || 0), 0);

  const selectedPackage = packages.find((pkg) => pkg.id === selectedPackageId);
  const packageTotal = selectedPackage?.price || 0;

  const total = activeTier === 'custom' ? customTotal : packageTotal;

  const handleContinue = () => {
    navigation.navigate('Checkout', {
      vendorId: vendor?.id,
      vendor,
      packageId: activeTier === 'custom' ? null : selectedPackage?.id,
      packageName: activeTier === 'custom' ? 'Custom Package' : selectedPackage?.name,
      services:
        activeTier === 'custom'
          ? selectedCustomItems.map((item) => item.name)
          : selectedPackage?.includes || [],
      totalAmount: total,
      tier: activeTier,
    });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.title}>Select Package</Title>
        {vendor?.business_name ? (
          <Paragraph style={styles.vendorName}>{vendor.business_name}</Paragraph>
        ) : null}
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsRow}>
        {tiers
          .filter((tier) => availableTiers.includes(tier))
          .map((tier) => (
            <Chip
              key={tier}
              mode={activeTier === tier ? 'flat' : 'outlined'}
              onPress={() => {
                setActiveTier(tier);
                setSelectedPackageId(null);
              }}
              style={styles.tabChip}
            >
              {tier.toUpperCase()}
            </Chip>
          ))}
      </ScrollView>

      {activeTier !== 'custom' && (
        <View style={styles.section}>
          {tierPackages.length === 0 ? (
            <Card style={styles.card}>
              <Card.Content>
                <Paragraph>No packages available for this tier.</Paragraph>
              </Card.Content>
            </Card>
          ) : (
            tierPackages.map((pkg) => (
              <Card key={pkg.id} style={styles.card} onPress={() => setSelectedPackageId(pkg.id)}>
                <Card.Content>
                  <View style={styles.cardHeader}>
                    <Title>{pkg.name}</Title>
                    <Chip mode="outlined">{pkg.tier?.toUpperCase()}</Chip>
                  </View>
                  <Text style={styles.price}>{formatCurrency(pkg.price)}</Text>
                  {pkg.description ? <Paragraph>{pkg.description}</Paragraph> : null}
                  {pkg.includes ? (
                    <Paragraph style={styles.includesText}>
                      What's included: {pkg.includes.join(', ')}
                    </Paragraph>
                  ) : null}
                  <View style={styles.selectRow}>
                    <Checkbox status={selectedPackageId === pkg.id ? 'checked' : 'unchecked'} />
                    <Text>Select this package</Text>
                  </View>
                </Card.Content>
              </Card>
            ))
          )}
        </View>
      )}

      {activeTier === 'custom' && (
        <View style={styles.section}>
          <Title style={styles.sectionTitle}>Build Your Custom Package</Title>
          {availableItems.map((item) => (
            <Card key={item.id} style={styles.card}>
              <Card.Content style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Title style={styles.itemName}>{item.name}</Title>
                  <Text style={styles.itemPrice}>{formatCurrency(item.price)}</Text>
                </View>
                <Checkbox
                  status={customItems[item.id] ? 'checked' : 'unchecked'}
                  onPress={() =>
                    setCustomItems((prev) => ({ ...prev, [item.id]: !prev[item.id] }))
                  }
                />
              </Card.Content>
            </Card>
          ))}
        </View>
      )}

      <View style={styles.summary}>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total</Text>
          <Text style={styles.summaryValue}>{formatCurrency(total)}</Text>
        </View>
        <Button
          mode="contained"
          onPress={handleContinue}
          disabled={activeTier !== 'custom' && !selectedPackageId}
          style={styles.cta}
        >
          Continue to Checkout
        </Button>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  header: {
    padding: 20,
  },
  title: {
    fontSize: 26,
  },
  vendorName: {
    color: '#78716C',
    marginTop: 4,
  },
  tabsRow: {
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  tabChip: {
    marginRight: 8,
  },
  section: {
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 20,
    marginBottom: 10,
  },
  card: {
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  price: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#BE185D',
    marginBottom: 6,
  },
  includesText: {
    color: '#78716C',
    marginTop: 6,
  },
  selectRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
  },
  itemPrice: {
    color: '#78716C',
    marginTop: 4,
  },
  summary: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#E7E5E4',
    backgroundColor: '#FFFFFF',
    marginTop: 10,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 16,
    color: '#78716C',
  },
  summaryValue: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#BE185D',
  },
  cta: {
    paddingVertical: 6,
  },
});

export default PackageSelectionScreen;
