import React, { useEffect, useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { TextInput, Button, Card, Title } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { categories, vendorRegister } from '../services/api';

const AuthScreen = ({ navigation }) => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    businessName: '',
    city: '',
    categoryId: '',
  });
  const [accountType, setAccountType] = useState('customer');
  const [categoryList, setCategoryList] = useState([]);

  useEffect(() => {
    categories
      .getAll()
      .then((res) => {
        const payload = res?.data?.data || res?.data || [];
        setCategoryList(Array.isArray(payload) ? payload : []);
      })
      .catch(() => setCategoryList([]));
  }, []);

  const normalizePhone = (value) => {
    const digits = (value || '').replace(/\D/g, '');
    if (digits.length === 12 && digits.startsWith('91')) return digits.slice(2);
    return digits;
  };

  const handleSubmit = async () => {
    if (!isLogin) {
      if ((formData.password || '').length < 8) {
        alert('Password must be at least 8 characters');
        return;
      }
      const normalizedPhone = normalizePhone(formData.phone);
      if (normalizedPhone && normalizedPhone.length !== 10) {
        alert('Phone number must be exactly 10 digits');
        return;
      }
      if (accountType === 'vendor') {
        if (!(formData.businessName || '').trim()) {
          alert('Business name is required for vendor');
          return;
        }
        if (!(formData.city || '').trim()) {
          alert('City is required for vendor');
          return;
        }
        if (!(formData.categoryId || '').trim()) {
          alert('Category ID is required for vendor');
          return;
        }
      }
    }

    setLoading(true);
    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        if (accountType === 'vendor') {
          await vendorRegister.register({
            business_name: formData.businessName.trim(),
            owner_name: formData.name.trim(),
            email: formData.email.trim(),
            phone: normalizePhone(formData.phone),
            password: formData.password,
            category_id: formData.categoryId.trim(),
            city: formData.city.trim(),
            service_areas: [formData.city.trim()],
            highlights: [],
            details: {},
          });
          // Ensure auth context/token are set via standard login flow
          await login(formData.email, formData.password);
        } else {
          await register({
            name: formData.name,
            email: formData.email,
            password: formData.password,
            phone: normalizePhone(formData.phone),
            role: 'customer',
          });
        }
      }
      navigation.replace('Tabs');
    } catch (error) {
      console.error('Auth error:', error);
      alert(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.title}>
            {isLogin ? 'Login to Shadiro' : 'Create Account'}
          </Title>

          {!isLogin && (
            <View style={styles.typeRow}>
              <Button
                mode={accountType === 'customer' ? 'contained' : 'outlined'}
                onPress={() => setAccountType('customer')}
                style={styles.typeButton}
              >
                Customer
              </Button>
              <Button
                mode={accountType === 'vendor' ? 'contained' : 'outlined'}
                onPress={() => setAccountType('vendor')}
                style={styles.typeButton}
              >
                Vendor
              </Button>
            </View>
          )}

          {!isLogin && (
            <TextInput
              label="Full Name"
              value={formData.name}
              onChangeText={(text) => setFormData({ ...formData, name: text })}
              style={styles.input}
              mode="outlined"
            />
          )}

          {!isLogin && accountType === 'vendor' && (
            <>
              <TextInput
                label="Business Name"
                value={formData.businessName}
                onChangeText={(text) => setFormData({ ...formData, businessName: text })}
                style={styles.input}
                mode="outlined"
              />
              <TextInput
                label="City"
                value={formData.city}
                onChangeText={(text) => setFormData({ ...formData, city: text })}
                style={styles.input}
                mode="outlined"
              />
              <Title style={styles.categoryTitle}>Select Category</Title>
              {categoryList.length > 0 && (
                <View style={styles.categoryWrap}>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    {categoryList.map((cat) => {
                      const id = String(cat?.id || '');
                      const name = String(cat?.name || cat?.slug || id);
                      const selected = formData.categoryId === id;
                      return (
                        <Button
                          key={id}
                          mode={selected ? 'contained' : 'outlined'}
                          compact
                          style={styles.categoryChip}
                          onPress={() => setFormData({ ...formData, categoryId: id })}
                        >
                          {name}
                        </Button>
                      );
                    })}
                  </ScrollView>
                </View>
              )}
              {categoryList.length === 0 && (
                <TextInput
                  label="Category ID (fallback)"
                  value={formData.categoryId}
                  onChangeText={(text) => setFormData({ ...formData, categoryId: text })}
                  style={styles.input}
                  mode="outlined"
                  autoCapitalize="none"
                />
              )}
            </>
          )}

          <TextInput
            label="Email"
            value={formData.email}
            onChangeText={(text) => setFormData({ ...formData, email: text })}
            keyboardType="email-address"
            autoCapitalize="none"
            style={styles.input}
            mode="outlined"
          />

          {!isLogin && (
            <TextInput
              label="Phone"
              value={formData.phone}
              onChangeText={(text) => setFormData({ ...formData, phone: text })}
              keyboardType="phone-pad"
              style={styles.input}
              mode="outlined"
            />
          )}

          <TextInput
            label="Password"
            value={formData.password}
            onChangeText={(text) => setFormData({ ...formData, password: text })}
            secureTextEntry
            style={styles.input}
            mode="outlined"
          />

          <Button
            mode="contained"
            onPress={handleSubmit}
            loading={loading}
            disabled={loading}
            style={styles.button}
          >
            {isLogin ? 'Login' : 'Register'}
          </Button>

          <Button
            mode="text"
            onPress={() => setIsLogin(!isLogin)}
            style={styles.switchButton}
          >
            {isLogin ? "Don't have an account? Register" : 'Already have an account? Login'}
          </Button>
        </Card.Content>
      </Card>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#FAFAF9',
  },
  card: {
    elevation: 4,
  },
  title: {
    textAlign: 'center',
    marginBottom: 20,
    fontSize: 24,
  },
  input: {
    marginBottom: 15,
  },
  typeRow: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  typeButton: {
    flex: 1,
    marginHorizontal: 5,
  },
  categoryWrap: {
    marginBottom: 15,
  },
  categoryTitle: {
    fontSize: 14,
    marginBottom: 8,
  },
  categoryChip: {
    marginRight: 8,
  },
  button: {
    marginTop: 10,
    paddingVertical: 8,
  },
  switchButton: {
    marginTop: 10,
  },
});

export default AuthScreen;
