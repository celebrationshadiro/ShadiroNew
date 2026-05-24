import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Card, Title, Paragraph, TextInput, Button, ActivityIndicator } from 'react-native-paper';
import { quotes, assistant } from '../../services/api';

const VendorQuoteRespondScreen = ({ route, navigation }) => {
  const { quoteId } = route.params;
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tone, setTone] = useState('formal');
  const [responseMessage, setResponseMessage] = useState('');
  const [quotedPrice, setQuotedPrice] = useState('');
  const [servicesOffered, setServicesOffered] = useState('');
  const [draftMeta, setDraftMeta] = useState(null);
  const [draftLoading, setDraftLoading] = useState(false);

  const loadQuote = async () => {
    setLoading(true);
    try {
      const res = await quotes.getAll();
      const found = res.data?.find((q) => q.id === quoteId);
      setQuote(found || null);
      setServicesOffered((found?.requested_services || []).join(', '));
    } catch (error) {
      console.error('Failed to load quote', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuote();
  }, [quoteId]);

  const handleGenerateDraft = async () => {
    if (!quote) return;
    setDraftLoading(true);
    try {
      const res = await assistant.draftQuote({
        quote_id: quote.id,
        tone,
        requested_services: quote.requested_services || [],
      });
      const data = res.data;
      if (data?.draft) {
        setResponseMessage(data.draft);
      }
      if (!quotedPrice && data?.suggested_price) {
        setQuotedPrice(String(data.suggested_price));
      }
      setDraftMeta(data || null);
    } catch (error) {
      console.error('Failed to generate draft', error);
    } finally {
      setDraftLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!quote) return;
    const priceValue = Number(quotedPrice);
    if (!quotedPrice || Number.isNaN(priceValue)) {
      return;
    }
    try {
      await quotes.respond(quote.id, {
        quoted_price: priceValue,
        response_message: responseMessage || null,
        services_offered: servicesOffered
          ? servicesOffered.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
      });
      navigation.goBack();
    } catch (error) {
      console.error('Failed to respond to quote', error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#BE185D" />
      </View>
    );
  }

  if (!quote) {
    return (
      <View style={styles.loadingContainer}>
        <Paragraph>Quote not found.</Paragraph>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Quote Details</Title>
          <Paragraph>Services: {(quote.requested_services || []).join(', ') || 'Custom request'}</Paragraph>
          {quote.message ? <Paragraph>Message: {quote.message}</Paragraph> : null}
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Title>Compose Response</Title>
          <View style={styles.toneRow}>
            <Button mode={tone === 'formal' ? 'contained' : 'outlined'} onPress={() => setTone('formal')}>
              Formal
            </Button>
            <Button mode={tone === 'quick' ? 'contained' : 'outlined'} onPress={() => setTone('quick')}>
              Quick
            </Button>
            <Button mode={tone === 'concise' ? 'contained' : 'outlined'} onPress={() => setTone('concise')}>
              Concise
            </Button>
          </View>
          <Button mode="outlined" onPress={handleGenerateDraft} loading={draftLoading} style={styles.cta}>
            Generate Draft
          </Button>
          {draftMeta ? (
            <Paragraph style={styles.metaText}>{draftMeta.reasoning}</Paragraph>
          ) : null}
          <TextInput
            label="Quoted Price (INR)"
            value={quotedPrice}
            onChangeText={setQuotedPrice}
            mode="outlined"
            style={styles.input}
            keyboardType="numeric"
          />
          <TextInput
            label="Services Offered"
            value={servicesOffered}
            onChangeText={setServicesOffered}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="Response Message"
            value={responseMessage}
            onChangeText={setResponseMessage}
            mode="outlined"
            style={styles.input}
            multiline
            numberOfLines={4}
          />
          <Button mode="contained" onPress={handleSubmit} style={styles.cta}>
            Send Response
          </Button>
        </Card.Content>
      </Card>
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
    marginBottom: 16,
  },
  input: {
    marginTop: 12,
  },
  cta: {
    marginTop: 12,
  },
  toneRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  metaText: {
    marginTop: 12,
    color: '#6B7280',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FAFAF9',
  },
});

export default VendorQuoteRespondScreen;
