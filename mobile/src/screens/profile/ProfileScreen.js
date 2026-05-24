import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, Card, Title, Paragraph, Chip } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';

const ProfileScreen = ({ navigation }) => {
  const { user, isAuthenticated, role, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigation.navigate('Home');
  };

  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Profile</Title>
          {isAuthenticated ? (
            <>
              <Paragraph style={styles.name}>{user?.name}</Paragraph>
              <Paragraph>{user?.email}</Paragraph>
              <View style={styles.roleRow}>
                <Text style={styles.roleLabel}>Role</Text>
                <Chip style={styles.roleChip}>{role}</Chip>
              </View>
              <Button mode="outlined" onPress={handleLogout} style={styles.cta}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Paragraph>You are not logged in.</Paragraph>
              <Button
                mode="contained"
                onPress={() => navigation.navigate('Auth')}
                style={styles.cta}
              >
                Login / Register
              </Button>
            </>
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
  name: {
    marginTop: 8,
    fontSize: 18,
  },
  roleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    gap: 8,
  },
  roleLabel: {
    color: '#78716C',
  },
  roleChip: {
    backgroundColor: '#F3E8FF',
  },
  cta: {
    marginTop: 16,
  },
});

export default ProfileScreen;
