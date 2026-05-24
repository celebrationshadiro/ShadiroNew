import React, { useState } from 'react';
import { View, ScrollView, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Title, HelperText } from 'react-native-paper';
import { Picker } from '@react-native-picker/picker';
import { useAuth } from '../contexts/AuthContext';
import { events } from '../services/api';

const CreateEventScreen = ({ navigation }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    event_type: 'wedding',
    date: '',
    location: '',
    guest_count: '',
    budget_min: '',
    budget_max: '',
    description: '',
  });

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const eventData = {
        ...formData,
        user_id: user.id,
        guest_count: formData.guest_count ? parseInt(formData.guest_count) : null,
        budget_min: formData.budget_min ? parseFloat(formData.budget_min) : null,
        budget_max: formData.budget_max ? parseFloat(formData.budget_max) : null,
      };
      
      await events.create(eventData);
      alert('Event created successfully!');
      navigation.goBack();
    } catch (error) {
      console.error('Failed to create event:', error);
      alert(error.response?.data?.detail || 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView style={styles.scrollView}>
        <View style={styles.content}>
          <Title style={styles.title}>Create New Event</Title>

          <TextInput
            label="Event Title *"
            value={formData.title}
            onChangeText={(text) => setFormData({ ...formData, title: text })}
            style={styles.input}
            mode="outlined"
          />

          <View style={styles.pickerContainer}>
            <HelperText type="info">Event Type</HelperText>
            <Picker
              selectedValue={formData.event_type}
              onValueChange={(value) => setFormData({ ...formData, event_type: value })}
              style={styles.picker}
            >
              <Picker.Item label="Wedding" value="wedding" />
              <Picker.Item label="Corporate Event" value="corporate" />
              <Picker.Item label="Birthday Party" value="birthday" />
              <Picker.Item label="Anniversary" value="anniversary" />
              <Picker.Item label="Other" value="other" />
            </Picker>
          </View>

          <TextInput
            label="Event Date *"
            value={formData.date}
            onChangeText={(text) => setFormData({ ...formData, date: text })}
            placeholder="YYYY-MM-DD"
            style={styles.input}
            mode="outlined"
          />

          <TextInput
            label="Location"
            value={formData.location}
            onChangeText={(text) => setFormData({ ...formData, location: text })}
            style={styles.input}
            mode="outlined"
          />

          <TextInput
            label="Expected Guests"
            value={formData.guest_count}
            onChangeText={(text) => setFormData({ ...formData, guest_count: text })}
            keyboardType="numeric"
            style={styles.input}
            mode="outlined"
          />

          <TextInput
            label="Min Budget (₹)"
            value={formData.budget_min}
            onChangeText={(text) => setFormData({ ...formData, budget_min: text })}
            keyboardType="numeric"
            style={styles.input}
            mode="outlined"
          />

          <TextInput
            label="Max Budget (₹)"
            value={formData.budget_max}
            onChangeText={(text) => setFormData({ ...formData, budget_max: text })}
            keyboardType="numeric"
            style={styles.input}
            mode="outlined"
          />

          <TextInput
            label="Description"
            value={formData.description}
            onChangeText={(text) => setFormData({ ...formData, description: text })}
            multiline
            numberOfLines={4}
            style={styles.input}
            mode="outlined"
          />

          <Button
            mode="contained"
            onPress={handleSubmit}
            loading={loading}
            disabled={loading || !formData.title || !formData.date}
            style={styles.submitButton}
          >
            Create Event
          </Button>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF9',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    marginBottom: 20,
  },
  input: {
    marginBottom: 15,
  },
  pickerContainer: {
    marginBottom: 15,
  },
  picker: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 4,
  },
  submitButton: {
    marginTop: 20,
    paddingVertical: 8,
  },
});

export default CreateEventScreen;
