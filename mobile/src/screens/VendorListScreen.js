import React, { useState, useEffect, useCallback, memo } from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Text, Card, Title, Paragraph, Chip, ActivityIndicator, TextInput, Searchbar } from 'react-native-paper';
import { vendors } from '../services/api';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import LazyImage from '../components/LazyImage';
import { formatCurrency } from '../utils/formatters';

const VendorCard = memo(({ vendor, onPress }) => (
  <Card style={styles.vendorCard} onPress={onPress}>
    {vendor.media && vendor.media[0] && (
      <LazyImage source={{ uri: vendor.media[0].url }} style={styles.coverImage} />
    )}
    <Card.Content>
      <Title>{vendor.business_name}</Title>
      {vendor.location && <Paragraph>{vendor.location}</Paragraph>}
      <View style={styles.vendorInfo}>
        <Chip icon="star" style={styles.ratingChip}>
          {(vendor.rating ?? 4.5).toFixed?.(1) || '4.5'} ({vendor.total_reviews || 0})
        </Chip>
        {vendor.base_price && <Text style={styles.price}>{formatCurrency(vendor.base_price)}</Text>}
      </View>
      <View style={styles.badgeRow}>
        {vendor.is_verified && (
          <Chip icon="check-circle" mode="outlined" style={styles.verifiedChip}>
            Verified
          </Chip>
        )}
        {vendor.years_experience ? (
          <Chip mode="outlined" style={styles.metaChip}>
            {vendor.years_experience} yrs
          </Chip>
        ) : null}
        {vendor.completed_bookings ? (
          <Chip mode="outlined" style={styles.metaChip}>
            {vendor.completed_bookings} bookings
          </Chip>
        ) : null}
        {vendor.distance_km ? (
          <Chip icon="map-marker" mode="outlined" style={styles.metaChip}>
            {vendor.distance_km} km
          </Chip>
        ) : null}
      </View>
    </Card.Content>
  </Card>
));

const VendorListScreen = ({ navigation, route }) => {
  const [vendorList, setVendorList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const { categoryId, search } = route.params || {};
  const [searchQuery, setSearchQuery] = useState(search || '');
  const [locationQuery, setLocationQuery] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [availability, setAvailability] = useState('');
  const [activeCategoryId, setActiveCategoryId] = useState(categoryId || '');

  const renderVendorItem = useCallback(
    ({ item }) => (
      <VendorCard
        vendor={item}
        onPress={() => navigation.navigate('VendorDetail', { vendorId: item.id })}
      />
    ),
    [navigation]
  );

  useEffect(() => {
    resetAndLoad();
  }, [activeCategoryId, searchQuery, locationQuery, minPrice, maxPrice, availability]);

  const resetAndLoad = async () => {
    setPage(0);
    setHasMore(true);
    setVendorList([]);
    await loadVendors(0, true);
  };

  const loadVendors = async (pageIndex = 0, initial = false) => {
    if (loadingMore) return;
    if (initial) {
      setLoading(true);
      setError('');
    } else {
      setLoadingMore(true);
    }
    try {
      const params = {};
      if (activeCategoryId) params.category_id = activeCategoryId;
      if (searchQuery) params.search = searchQuery;
      if (locationQuery) params.location = locationQuery;
      if (minPrice) params.min_price = minPrice;
      if (maxPrice) params.max_price = maxPrice;
      if (availability) params.availability = availability;
      params.limit = 10;
      params.offset = pageIndex * 10;
      
      const response = await vendors.getAll(params);
      const newItems = response.data || [];
      setVendorList((prev) => (pageIndex === 0 ? newItems : [...prev, ...newItems]));
      setHasMore(newItems.length === 10);
      setPage(pageIndex);
    } catch (error) {
      console.error('Failed to load vendors:', error);
      setError('Unable to load vendors. Please try again.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <FlatList
          data={[1, 2, 3, 4, 5]}
          keyExtractor={(item) => item.toString()}
          renderItem={() => (
            <View style={styles.skeletonCard}>
              <View style={styles.skeletonImage} />
              <View style={styles.skeletonLine} />
              <View style={styles.skeletonLineShort} />
            </View>
          )}
          contentContainerStyle={styles.listContainer}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.filterContainer}>
        <Searchbar
          placeholder="Search vendors"
          value={searchQuery}
          onChangeText={setSearchQuery}
          style={styles.searchbar}
        />
        <TextInput
          label="Location"
          value={locationQuery}
          onChangeText={setLocationQuery}
          mode="outlined"
          style={styles.filterInput}
        />
        <View style={styles.priceRow}>
          <TextInput
            label="Min ₹"
            value={minPrice}
            onChangeText={setMinPrice}
            mode="outlined"
            keyboardType="numeric"
            style={[styles.filterInput, styles.priceInput]}
          />
          <TextInput
            label="Max ₹"
            value={maxPrice}
            onChangeText={setMaxPrice}
            mode="outlined"
            keyboardType="numeric"
            style={[styles.filterInput, styles.priceInput]}
          />
        </View>
        <View style={styles.chipRow}>
          {['available', 'busy', 'all'].map((status) => (
            <Chip
              key={status}
              mode={availability === status ? 'flat' : 'outlined'}
              onPress={() => setAvailability(status === 'all' ? '' : status)}
              style={styles.filterChip}
            >
              {status === 'all' ? 'Any Availability' : status}
            </Chip>
          ))}
        </View>
        {!!activeCategoryId && (
          <View style={styles.activeCategoryRow}>
            <Chip onClose={() => setActiveCategoryId('')}>
              Category: {activeCategoryId}
            </Chip>
          </View>
        )}
      </View>

      <FlatList
        data={vendorList}
        renderItem={renderVendorItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          error ? (
            <ErrorState title="Couldn’t load vendors" message={error} onRetry={resetAndLoad} />
          ) : (
            <EmptyState
              title="No vendors found"
              message="Try adjusting filters or search."
              actionLabel="Reset filters"
              onAction={() => {
                setSearchQuery('');
                setLocationQuery('');
                setMinPrice('');
                setMaxPrice('');
                setAvailability('');
                setActiveCategoryId('');
              }}
            />
          )
        }
        onEndReached={() => {
          if (hasMore && !loadingMore) {
            loadVendors(page + 1);
          }
        }}
        onEndReachedThreshold={0.4}
        removeClippedSubviews
        initialNumToRender={6}
        maxToRenderPerBatch={6}
        windowSize={7}
        ListFooterComponent={
          loadingMore ? (
            <View style={styles.loadingMore}>
              <ActivityIndicator size="small" color="#BE185D" />
            </View>
          ) : !hasMore && vendorList.length > 0 ? (
            <View style={styles.loadingMore}>
              <Text style={styles.endText}>No more vendors</Text>
            </View>
          ) : null
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  filterContainer: {
    padding: 15,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E7E5E4',
  },
  searchbar: {
    marginBottom: 10,
  },
  filterInput: {
    marginBottom: 10,
    backgroundColor: '#fff',
  },
  priceRow: {
    flexDirection: 'row',
    gap: 10,
  },
  priceInput: {
    flex: 1,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  filterChip: {
    backgroundColor: '#F5F5F4',
  },
  activeCategoryRow: {
    marginTop: 8,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  listContainer: {
    padding: 15,
  },
  coverImage: {
    height: 160,
  },
  vendorCard: {
    marginBottom: 15,
  },
  vendorInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 10,
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  ratingChip: {
    backgroundColor: '#FEF3C7',
  },
  price: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#BE185D',
  },
  verifiedChip: {
    borderColor: '#10B981',
  },
  metaChip: {
    backgroundColor: '#F5F5F4',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#78716C',
  },
  skeletonCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 15,
    padding: 12,
  },
  skeletonImage: {
    height: 140,
    backgroundColor: '#E7E5E4',
    borderRadius: 10,
    marginBottom: 10,
  },
  skeletonLine: {
    height: 16,
    backgroundColor: '#E7E5E4',
    borderRadius: 8,
    marginBottom: 8,
  },
  skeletonLineShort: {
    height: 12,
    width: '60%',
    backgroundColor: '#E7E5E4',
    borderRadius: 8,
  },
  loadingMore: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  endText: {
    color: '#78716C',
  },
});

export default VendorListScreen;
