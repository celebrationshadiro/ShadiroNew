import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Title, Paragraph, Chip } from 'react-native-paper';
import { vendors } from '../../services/api';

const AdminVendorsScreen = () => {
  const [vendorList, setVendorList] = useState([]);

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      const response = await vendors.getAll();
      setVendorList(response.data || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Title style={styles.sectionTitle}>Vendor Oversight</Title>
      {vendorList.length === 0 ? (
        <Card style={styles.card}>
          <Card.Content>
            <Paragraph>No vendors found.</Paragraph>
          </Card.Content>
        </Card>
      ) : (
        vendorList.map((vendor) => (
          <Card key={vendor.id} style={styles.card}>
            <Card.Content>
              <View style={styles.headerRow}>
                <Title>{vendor.business_name}</Title>
                {vendor.is_verified ? (
                  <Chip icon="check-circle">Verified</Chip>
                ) : (
                  <Chip>Pending</Chip>
                )}
              </View>
              <Paragraph>{vendor.location}</Paragraph>
              <Paragraph>
                Rating: {(vendor.rating ?? 4.5).toFixed?.(1) || '4.5'} • Reviews: {vendor.total_reviews || 0}
              </Paragraph>
            </Card.Content>
          </Card>
        ))
      )}
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
  sectionTitle: {
    fontSize: 20,
    marginBottom: 10,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
});

export default AdminVendorsScreen;
