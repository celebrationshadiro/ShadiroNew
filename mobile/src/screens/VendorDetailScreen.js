import React, { useState, useEffect } from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { Text, Card, Title, Paragraph, Button, Chip, ActivityIndicator, Portal, Modal, TextInput } from 'react-native-paper';
import { vendors, packages, events, quotes } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ErrorState from '../components/ErrorState';
import LazyImage from '../components/LazyImage';
import AssistantWidget from '../components/AssistantWidget';
import { formatCurrency } from '../utils/formatters';

const VendorDetailScreen = ({ navigation, route }) => {
  const { vendorId } = route.params;
  const { user } = useAuth();
  const [vendor, setVendor] = useState(null);
  const [packageList, setPackageList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quoteVisible, setQuoteVisible] = useState(false);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteForm, setQuoteForm] = useState({ title: '', date: '', location: '', message: '' });
  const [eventList, setEventList] = useState([]);
  const [selectedEventIds, setSelectedEventIds] = useState([]);
  const [attachmentUrl, setAttachmentUrl] = useState('');
  const [attachments, setAttachments] = useState([]);

  const canBook = vendor?.onboarding_status === 'complete' || (vendor?.onboarding_missing_required || []).length === 0;

  useEffect(() => {
    loadVendorDetails();
  }, [vendorId]);

  const loadVendorDetails = async () => {
    setLoading(true);
    try {
      const [vendorRes, packagesRes] = await Promise.all([
        vendors.getById(vendorId),
        packages.getAll({ vendor_id: vendorId }),
      ]);
      setVendor(vendorRes.data);
      setPackageList(packagesRes.data);
    } catch (error) {
      console.error('Failed to load vendor details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookNow = () => {
    if (!user) {
      navigation.navigate('Auth');
      return;
    }
    navigation.navigate('PackageSelection', { vendorId, vendor, packages: packageList });
  };

  const handleQuoteRequest = () => {
    if (!user) {
      navigation.navigate('Auth');
      return;
    }
    events.getAll()
      .then((res) => setEventList(res.data || []))
      .catch(() => setEventList([]));
    setSelectedEventIds([]);
    setQuoteVisible(true);
  };

  const submitQuoteRequest = async () => {
    if (selectedEventIds.length === 0 && (!quoteForm.title || !quoteForm.date)) return;
    setQuoteLoading(true);
    try {
      let eventIds = [...selectedEventIds];
      if (quoteForm.title && quoteForm.date) {
        const eventRes = await events.create({
          user_id: user.id,
          event_type: 'other',
          title: quoteForm.title,
          date: quoteForm.date,
          location: quoteForm.location || '',
        });
        const eventId = eventRes.data?.id || eventRes.data?._id;
        if (eventId) eventIds.push(eventId);
      }
      await Promise.all(eventIds.map((eventId) => quotes.create({
        event_id: eventId,
        vendor_id: vendor.id,
        user_id: user.id,
        requested_services: [],
        message: quoteForm.message || null,
        attachments,
      })));
      setQuoteVisible(false);
      setQuoteForm({ title: '', date: '', location: '', message: '' });
      setAttachments([]);
    } catch (error) {
      console.error('Failed to request quote:', error);
    } finally {
      setQuoteLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <View style={styles.skeletonCard}>
          <View style={styles.skeletonImage} />
          <View style={styles.skeletonLine} />
          <View style={styles.skeletonLineShort} />
        </View>
      </View>
    );
  }

  if (!vendor) {
    return (
      <View style={styles.container}>
        <ErrorState
          title="Vendor not found"
          message="This vendor is unavailable right now."
          onRetry={loadVendorDetails}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView>
      {vendor.media && vendor.media[0] && (
        <LazyImage source={{ uri: vendor.media[0].url }} style={styles.coverImage} />
      )}

      <View style={styles.content}>
        <View style={styles.header}>
          <Title style={styles.title}>{vendor.business_name}</Title>
          {vendor.is_verified && (
            <Chip icon="check-circle" style={styles.verifiedChip}>Verified</Chip>
          )}
        </View>

        {vendor.location && (
          <Paragraph style={styles.location}>{vendor.location}</Paragraph>
        )}

        <View style={styles.statsRow}>
          <Chip icon="star" style={styles.ratingChip}>
            {(vendor.rating ?? 4.5).toFixed?.(1) || '4.5'} ({vendor.total_reviews || 0} reviews)
          </Chip>
          {vendor.base_price && <Text style={styles.price}>{formatCurrency(vendor.base_price)}</Text>}
        </View>

        <View style={styles.trustRow}>
          {vendor.is_verified && (
            <Chip icon="check-circle" mode="outlined" style={styles.verifiedChip}>
              Verified
            </Chip>
          )}
          {vendor.years_experience ? (
            <Chip mode="outlined" style={styles.metaChip}>
              {vendor.years_experience} yrs experience
            </Chip>
          ) : null}
          {vendor.completed_bookings ? (
            <Chip mode="outlined" style={styles.metaChip}>
              {vendor.completed_bookings} bookings
            </Chip>
          ) : null}
          {vendor.distance_km ? (
            <Chip icon="map-marker" mode="outlined" style={styles.metaChip}>
              {vendor.distance_km} km away
            </Chip>
          ) : null}
        </View>

        {vendor.description && (
          <Card style={styles.descriptionCard}>
            <Card.Content>
              <Title style={styles.sectionTitle}>About</Title>
              <Paragraph>{vendor.description}</Paragraph>
            </Card.Content>
          </Card>
        )}

        {packageList.length > 0 && (
          <View style={styles.packagesSection}>
            <Title style={styles.sectionTitle}>Packages</Title>
            {packageList.map((pkg) => (
              <Card key={pkg.id} style={styles.packageCard}>
                <Card.Content>
                  <Chip style={styles.tierChip}>{pkg.tier.toUpperCase()}</Chip>
                  <Title>{pkg.name}</Title>
                  <Text style={styles.packagePrice}>{formatCurrency(pkg.price)}</Text>
                  {pkg.description && <Paragraph>{pkg.description}</Paragraph>}
                  {pkg.includes && (
                    <Paragraph style={styles.includesText}>
                      What's included: {pkg.includes.join(', ')}
                    </Paragraph>
                  )}
                </Card.Content>
              </Card>
            ))}
          </View>
        )}

        {(vendor.grocery_items?.length || vendor.dj_packages?.length || vendor.caterer_menu_items?.length || vendor.decorator_themes?.length) && (
          <View style={styles.packagesSection}>
            <Title style={styles.sectionTitle}>Services & Items</Title>
            {vendor.grocery_items?.map((item) => (
              <Card key={item.id} style={styles.packageCard}>
                <Card.Content>
                  <Title>{item.name}</Title>
                  <Paragraph>{item.category || 'Grocery item'} • {item.availability}</Paragraph>
                  <Text style={styles.packagePrice}>{formatCurrency(item.unit_price)} / {item.unit}</Text>
                </Card.Content>
              </Card>
            ))}
            {vendor.dj_packages?.map((pkg) => (
              <Card key={pkg.id} style={styles.packageCard}>
                <Card.Content>
                  <Title>{pkg.name}</Title>
                  <Paragraph>{pkg.duration_hours} hours</Paragraph>
                  <Text style={styles.packagePrice}>{formatCurrency(pkg.price)}</Text>
                </Card.Content>
              </Card>
            ))}
            {vendor.caterer_menu_items?.map((item) => (
              <Card key={item.id} style={styles.packageCard}>
                <Card.Content>
                  <Title>{item.name}</Title>
                  <Paragraph>{item.category || 'Menu item'}</Paragraph>
                  <Text style={styles.packagePrice}>{formatCurrency(item.unit_price)}</Text>
                </Card.Content>
              </Card>
            ))}
            {vendor.decorator_themes?.map((theme) => (
              <Card key={theme.id} style={styles.packageCard}>
                <Card.Content>
                  <Title>{theme.name}</Title>
                  {theme.description && <Paragraph>{theme.description}</Paragraph>}
                  {theme.price ? <Text style={styles.packagePrice}>{formatCurrency(theme.price)}</Text> : null}
                </Card.Content>
              </Card>
            ))}
          </View>
        )}

        <View style={styles.actions}>
          {canBook ? (
            <Button
              mode="contained"
              onPress={handleBookNow}
              style={styles.bookButton}
              icon="calendar"
            >
              Select Package
            </Button>
          ) : (
            <Card style={styles.noticeCard}>
              <Card.Content>
                <Paragraph>Booking is temporarily unavailable while this vendor completes onboarding.</Paragraph>
              </Card.Content>
            </Card>
          )}
          <Button
            mode="outlined"
            onPress={handleQuoteRequest}
            style={styles.chatButton}
            icon="file-document"
          >
            Request Quote
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('Chat', { vendorId })}
            style={styles.chatButton}
            icon="message"
          >
            Chat with Vendor
          </Button>
        </View>
      </View>
      </ScrollView>
      <Portal>
        <Modal visible={quoteVisible} onDismiss={() => setQuoteVisible(false)} contentContainerStyle={styles.modal}>
          <Title style={styles.modalTitle}>Request a Quote</Title>
          {eventList.length > 0 && (
            <View style={styles.eventList}>
              <Paragraph style={styles.eventLabel}>Select Existing Events</Paragraph>
              {eventList.map((event) => {
                const id = event.id || event._id;
                const selected = selectedEventIds.includes(id);
                return (
                  <Chip
                    key={id}
                    selected={selected}
                    onPress={() => {
                      if (selected) {
                        setSelectedEventIds(selectedEventIds.filter((item) => item !== id));
                      } else {
                        setSelectedEventIds([...selectedEventIds, id]);
                      }
                    }}
                    style={styles.eventChip}
                  >
                    {event.title} • {event.date}
                  </Chip>
                );
              })}
            </View>
          )}
          <TextInput
            label="Event Title"
            value={quoteForm.title}
            onChangeText={(text) => setQuoteForm({ ...quoteForm, title: text })}
            style={styles.input}
          />
          <TextInput
            label="Event Date (YYYY-MM-DD)"
            value={quoteForm.date}
            onChangeText={(text) => setQuoteForm({ ...quoteForm, date: text })}
            style={styles.input}
          />
          <TextInput
            label="Location"
            value={quoteForm.location}
            onChangeText={(text) => setQuoteForm({ ...quoteForm, location: text })}
            style={styles.input}
          />
          <TextInput
            label="Message"
            value={quoteForm.message}
            onChangeText={(text) => setQuoteForm({ ...quoteForm, message: text })}
            style={styles.input}
            multiline
          />
          <TextInput
            label="Attachment URL"
            value={attachmentUrl}
            onChangeText={setAttachmentUrl}
            style={styles.input}
          />
          <Button
            mode="outlined"
            onPress={() => {
              if (!attachmentUrl) return;
              setAttachments([...attachments, { url: attachmentUrl }]);
              setAttachmentUrl('');
            }}
            style={styles.attachButton}
          >
            Add Attachment
          </Button>
          {attachments.length > 0 && (
            <View style={styles.attachmentList}>
              {attachments.map((file, idx) => (
                <Paragraph key={`${file.url}-${idx}`}>{file.url}</Paragraph>
              ))}
            </View>
          )}
          <Button mode="contained" onPress={submitQuoteRequest} loading={quoteLoading}>
            Send Quote Request
          </Button>
        </Modal>
      </Portal>
      <AssistantWidget role="user" context={{ vendor }} title="Event Planning Assistant" />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  skeletonCard: {
    width: '90%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
  },
  skeletonImage: {
    height: 180,
    backgroundColor: '#E7E5E4',
    borderRadius: 12,
    marginBottom: 12,
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
  coverImage: {
    height: 250,
  },
  content: {
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  title: {
    fontSize: 28,
    flex: 1,
  },
  verifiedChip: {
    backgroundColor: '#10B981',
  },
  location: {
    fontSize: 16,
    color: '#78716C',
    marginBottom: 15,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  trustRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
  },
  ratingChip: {
    backgroundColor: '#FEF3C7',
  },
  price: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#BE185D',
  },
  descriptionCard: {
    marginBottom: 20,
  },
  metaChip: {
    backgroundColor: '#F5F5F4',
  },
  sectionTitle: {
    fontSize: 22,
    marginBottom: 10,
  },
  packagesSection: {
    marginBottom: 20,
  },
  packageCard: {
    marginBottom: 10,
  },
  tierChip: {
    alignSelf: 'flex-start',
    marginBottom: 10,
    backgroundColor: '#F3E8FF',
  },
  packagePrice: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#BE185D',
    marginVertical: 5,
  },
  includesText: {
    marginTop: 8,
    color: '#78716C',
  },
  actions: {
    marginTop: 20,
    gap: 10,
  },
  bookButton: {
    paddingVertical: 8,
  },
  chatButton: {
    paddingVertical: 8,
    marginTop: 10,
  },
  modal: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    padding: 16,
    borderRadius: 16,
  },
  modalTitle: {
    marginBottom: 12,
  },
  input: {
    marginBottom: 10,
  },
  eventList: {
    marginBottom: 10,
  },
  eventLabel: {
    marginBottom: 6,
  },
  eventChip: {
    marginBottom: 6,
  },
  attachButton: {
    marginBottom: 10,
  },
  attachmentList: {
    marginBottom: 12,
  },
  noticeCard: {
    padding: 8,
    backgroundColor: '#FEF3C7',
  },
});

export default VendorDetailScreen;
