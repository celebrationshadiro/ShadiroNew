import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Card, Title, Paragraph, Button, ActivityIndicator } from 'react-native-paper';
import { quotes } from '../../services/api';

const VendorQuotesScreen = ({ navigation }) => {
  const [quoteList, setQuoteList] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadQuotes = async () => {
    setLoading(true);
    try {
      const res = await quotes.getAll();
      setQuoteList(res.data || []);
    } catch (error) {
      console.error('Failed to load quotes', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuotes();
  }, []);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#BE185D" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {quoteList.length === 0 ? (
        <Card style={styles.card}>
          <Card.Content>
            <Title>No Quote Requests</Title>
            <Paragraph>New quote requests will appear here.</Paragraph>
          </Card.Content>
        </Card>
      ) : (
        quoteList.map((quote) => (
          <Card key={quote.id} style={styles.card}>
            <Card.Content>
              <Title>Quote Request</Title>
              <Paragraph>Services: {(quote.requested_services || []).join(', ') || 'Custom request'}</Paragraph>
              {quote.message ? <Paragraph>Message: {quote.message}</Paragraph> : null}
              <Paragraph>Status: {quote.status}</Paragraph>
              {quote.lead_score_label ? (
                <Paragraph style={styles.leadBadge}>
                  {quote.lead_score_label} Lead {quote.lead_score !== undefined ? `· ${quote.lead_score}` : ''}
                </Paragraph>
              ) : null}
            </Card.Content>
            <Card.Actions>
              <Button onPress={() => navigation.navigate('VendorQuoteRespond', { quoteId: quote.id })}>
                Respond
              </Button>
            </Card.Actions>
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
    marginBottom: 16,
  },
  leadBadge: {
    marginTop: 6,
    color: '#BE185D',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FAFAF9',
  },
});

export default VendorQuotesScreen;
