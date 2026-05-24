import React, { useState, useEffect, memo } from 'react';
import { View, ScrollView, StyleSheet, TouchableOpacity, FlatList } from 'react-native';
import { Text, Card, Title, Paragraph, Button, Searchbar, Chip } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { categories, vendors } from '../services/api';
import { luxuryColors, luxuryTypography } from '../theme/luxuryTheme';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import LazyImage from '../components/LazyImage';

const CategoryCard = memo(({ category, onPress }) => (
  <TouchableOpacity onPress={onPress} style={styles.categoryCard}>
    <Card>
      <LazyImage source={{ uri: category.image_url }} style={styles.categoryImage} />
      <Card.Content style={styles.categoryContent}>
        <Title>{category.name}</Title>
        <Paragraph>{category.description}</Paragraph>
      </Card.Content>
    </Card>
  </TouchableOpacity>
));

const VendorMiniCard = memo(({ vendor, onPress }) => (
  <TouchableOpacity onPress={onPress} style={styles.vendorMiniCard}>
    <Card>
      {vendor.media && vendor.media[0] && (
        <LazyImage source={{ uri: vendor.media[0].url }} style={styles.vendorMiniImage} />
      )}
      <Card.Content>
        <Title style={styles.vendorMiniTitle}>{vendor.business_name}</Title>
        {vendor.location && <Paragraph style={styles.vendorMiniLocation}>{vendor.location}</Paragraph>}
        <View style={styles.vendorMiniMeta}>
          <Chip icon="star" style={styles.ratingChip}>
            {vendor.rating?.toFixed?.(1) || '4.5'}
          </Chip>
          {vendor.distance_km ? (
            <Chip icon="map-marker" style={styles.nearChip}>
              {vendor.distance_km} km
            </Chip>
          ) : null}
        </View>
      </Card.Content>
    </Card>
  </TouchableOpacity>
));

const HomeScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [categoryList, setCategoryList] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [popularVendors, setPopularVendors] = useState([]);
  const [error, setError] = useState('');
  const [loadingPopular, setLoadingPopular] = useState(true);

  useEffect(() => {
    loadCategories();
    loadPopularVendors();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await categories.getAll();
      setCategoryList(response.data);
    } catch (error) {
      console.error('Failed to load categories:', error);
      setError('Unable to load categories.');
    }
  };

  const loadPopularVendors = async () => {
    setLoadingPopular(true);
    try {
      const response = await vendors.getAll({ sort: 'popular', limit: 6 });
      setPopularVendors(response.data || []);
    } catch (error) {
      console.error('Failed to load popular vendors:', error);
      setError('Unable to load popular vendors.');
    } finally {
      setLoadingPopular(false);
    }
  };

  const handleSearch = () => {
    navigation.navigate('Explore', { search: searchQuery });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.headerTitle}>Plan Your Dream Event</Title>
        <Paragraph style={styles.headerText}>
          Connect with verified vendors for your special day
        </Paragraph>

        <Searchbar
          placeholder="Search vendors, venues..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          onSubmitEditing={handleSearch}
          style={styles.searchbar}
        />

        {!user && (
          <Button
            mode="contained"
            onPress={() => navigation.navigate('Auth')}
            style={styles.loginButton}
          >
            Login / Register
          </Button>
        )}

        {user && (
          <TouchableOpacity
            activeOpacity={0.92}
            onPress={() => navigation.navigate('DeliveryPartnerDashboard')}
            style={styles.logisticsCard}
          >
            <Text style={styles.logisticsKicker}>Shadiro Logistics</Text>
            <Text style={styles.logisticsTitle}>Delivery partner hub</Text>
            <Text style={styles.logisticsBody}>Premium routing, secure QR pickup, live tracking.</Text>
            <Text style={styles.logisticsCta}>Open hub →</Text>
          </TouchableOpacity>
        )}

        {user && (
          <Button
            mode="contained"
            onPress={() => navigation.navigate('Bookings')}
            style={styles.dashboardButton}
          >
            Go to Dashboard
          </Button>
        )}
      </View>

      <View style={styles.categoriesSection}>
        {error ? (
          <ErrorState title="Home data failed" message={error} onRetry={() => {
            setError('');
            loadCategories();
            loadPopularVendors();
          }} />
        ) : loadingPopular ? (
          <FlatList
            data={[1, 2, 3]}
            horizontal
            showsHorizontalScrollIndicator={false}
            keyExtractor={(item) => item.toString()}
            renderItem={() => (
              <View style={styles.skeletonCard}>
                <View style={styles.skeletonImage} />
                <View style={styles.skeletonLine} />
                <View style={styles.skeletonLineShort} />
              </View>
            )}
          />
        ) : popularVendors.length > 0 ? (
          <View style={styles.popularSection}>
            <Title style={styles.sectionTitle}>Popular near you</Title>
            <FlatList
              data={popularVendors}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <VendorMiniCard
                  vendor={item}
                  onPress={() => navigation.navigate('VendorDetail', { vendorId: item.id })}
                />
              )}
            />
          </View>
        ) : (
          <EmptyState
            title="No popular vendors yet"
            message="Check back soon or explore categories."
            actionLabel="Explore vendors"
            onAction={() => navigation.navigate('Explore')}
          />
        )}
        <Title style={styles.sectionTitle}>Browse by Category</Title>
        {categoryList.map((category) => (
          <CategoryCard
            key={category.id}
            category={category}
            onPress={() => navigation.navigate('Explore', { categoryId: category.id })}
          />
        ))}
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
    backgroundColor: '#BE185D',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  headerText: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 20,
  },
  searchbar: {
    marginBottom: 15,
  },
  loginButton: {
    marginTop: 10,
  },
  dashboardButton: {
    marginTop: 10,
    backgroundColor: '#F59E0B',
  },
  logisticsCard: {
    marginTop: 16,
    padding: 16,
    borderRadius: 16,
    backgroundColor: luxuryColors.matteBlack,
    borderWidth: 1,
    borderColor: luxuryColors.champagneGoldMuted,
  },
  logisticsKicker: {
    color: luxuryColors.champagneGold,
    fontSize: 11,
    letterSpacing: 2,
    textTransform: 'uppercase',
  },
  logisticsTitle: {
    ...luxuryTypography.display,
    color: luxuryColors.ivory,
    fontSize: 20,
    marginTop: 6,
  },
  logisticsBody: {
    ...luxuryTypography.body,
    color: luxuryColors.ivoryMuted,
    marginTop: 6,
    fontSize: 14,
  },
  logisticsCta: {
    marginTop: 10,
    color: luxuryColors.champagneGold,
    fontWeight: '600',
  },
  categoriesSection: {
    padding: 20,
  },
  popularSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 24,
    marginBottom: 15,
  },
  categoryCard: {
    marginBottom: 15,
  },
  categoryImage: {
    height: 160,
  },
  categoryContent: {
    paddingTop: 10,
  },
  vendorMiniCard: {
    width: 220,
    marginRight: 12,
  },
  vendorMiniImage: {
    height: 120,
  },
  vendorMiniTitle: {
    fontSize: 16,
  },
  vendorMiniLocation: {
    color: '#78716C',
  },
  vendorMiniMeta: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  nearChip: {
    backgroundColor: '#F5F5F4',
  },
  skeletonCard: {
    width: 220,
    marginRight: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
  },
  skeletonImage: {
    height: 120,
    backgroundColor: '#E7E5E4',
    borderRadius: 10,
    marginBottom: 10,
  },
  skeletonLine: {
    height: 14,
    backgroundColor: '#E7E5E4',
    borderRadius: 8,
    marginBottom: 6,
  },
  skeletonLineShort: {
    height: 12,
    width: '60%',
    backgroundColor: '#E7E5E4',
    borderRadius: 8,
  },
});

export default HomeScreen;
