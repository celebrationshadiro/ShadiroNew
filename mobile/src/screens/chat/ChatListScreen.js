import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, Card, Title, Paragraph } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';

const ChatListScreen = ({ navigation }) => {
  const { isAuthenticated } = useAuth();

  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Chats</Title>
          <Paragraph>
            Your conversations with vendors will appear here.
          </Paragraph>
          {!isAuthenticated ? (
            <Button
              mode="contained"
              onPress={() => navigation.navigate('Auth')}
              style={styles.cta}
            >
              Login to view chats
            </Button>
          ) : (
            <Button
              mode="outlined"
              onPress={() => navigation.navigate('Explore')}
              style={styles.cta}
            >
              Find vendors to chat
            </Button>
          )}
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
    marginTop: 16,
  },
});

export default ChatListScreen;
