import React, { useMemo, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Text, TextInput, Button, Chip, FAB, IconButton, Surface } from 'react-native-paper';
import { assistant } from '../services/api';
import { luxuryColors, luxuryTypography } from '../theme/luxuryTheme';

const DEFAULT_SUGGESTIONS = [
  'Help me shortlist vendors',
  'Build a booking checklist',
  'Suggest a delivery-friendly timeline',
];

const buildContextPayload = (context) => {
  if (!context) return {};
  const payload = { ...context };
  if (context.vendor) {
    payload.profile = context.vendor;
    payload.category_id = context.vendor.category_id || context.category_id;
  }
  return payload;
};

/**
 * Premium concierge assistant: full-screen immersive mode, smooth minimize to dock,
 * persistent FAB when dismissed (no abrupt exits).
 */
const AssistantWidget = ({ title = 'Shadiro Concierge', role = 'user', context }) => {
  const [mode, setMode] = useState('fab');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState('en');
  const [messages, setMessages] = useState([
    { from: 'assistant', text: 'Welcome. I am your personal concierge for weddings, vendors, and deliveries.' },
  ]);
  const [suggestions, setSuggestions] = useState(DEFAULT_SUGGESTIONS);

  const payloadBase = useMemo(() => buildContextPayload(context), [context]);

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = (text || '').trim();
      if (!trimmed) return;
      setMessages((prev) => [...prev, { from: 'user', text: trimmed }]);
      setMessage('');
      setLoading(true);
      try {
        const res = await assistant.message({
          message: trimmed,
          role,
          language: lang,
          ...payloadBase,
        });
        const data = res?.data || {};
        setMessages((prev) => [...prev, { from: 'assistant', text: data.reply || 'Noted. How else may I assist you?' }]);
        if (Array.isArray(data.suggestions) && data.suggestions.length > 0) {
          setSuggestions(data.suggestions);
        }
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          { from: 'assistant', text: 'The concierge is momentarily unavailable. Please try again shortly.' },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [lang, role, payloadBase],
  );

  const openFull = () => setMode('full');
  const minimizeToDock = () => setMode('dock');
  const hideDock = () => setMode('fab');

  return (
    <>
      {mode === 'fab' ? (
        <FAB
          icon="auto-fix"
          color={luxuryColors.matteBlack}
          style={styles.fab}
          onPress={openFull}
          label="Concierge"
        />
      ) : null}

      {mode === 'dock' ? (
        <Surface style={styles.dock} elevation={6}>
          <TouchableOpacity style={styles.dockInner} onPress={openFull} activeOpacity={0.9}>
            <Text style={styles.dockTitle}>Concierge</Text>
            <Text style={styles.dockHint}>Tap to expand</Text>
          </TouchableOpacity>
          <IconButton icon="chevron-up" size={22} onPress={openFull} iconColor={luxuryColors.champagneGold} />
          <IconButton icon="close" size={20} onPress={hideDock} iconColor={luxuryColors.ivoryMuted} />
        </Surface>
      ) : null}

      <Modal
        visible={mode === 'full'}
        animationType="slide"
        transparent
        onRequestClose={minimizeToDock}
      >
        <Pressable style={styles.backdrop} onPress={minimizeToDock}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={styles.sheetWrap}
          >
            <Pressable onPress={(e) => e.stopPropagation()}>
              <View style={styles.sheet}>
                <View style={styles.sheetHeader}>
                  <View>
                    <Text style={styles.sheetKicker}>Shadiro</Text>
                    <Text style={styles.sheetTitle}>{title}</Text>
                  </View>
                  <View style={styles.headerActions}>
                    <Chip compact selected={lang === 'en'} onPress={() => setLang('en')} style={styles.langChip}>
                      EN
                    </Chip>
                    <Chip compact selected={lang === 'hi'} onPress={() => setLang('hi')} style={styles.langChip}>
                      HI
                    </Chip>
                    <IconButton
                      icon="minus"
                      accessibilityLabel="Minimize concierge"
                      onPress={minimizeToDock}
                      iconColor={luxuryColors.ivory}
                    />
                  </View>
                </View>

                <ScrollView style={styles.messages} keyboardShouldPersistTaps="handled">
                  {messages.slice(-20).map((msg, idx) => (
                    <View
                      key={`${msg.from}-${idx}`}
                      style={msg.from === 'assistant' ? styles.messageLeft : styles.messageRight}
                    >
                      <Text style={msg.from === 'assistant' ? styles.bubbleLeft : styles.bubbleRight}>{msg.text}</Text>
                    </View>
                  ))}
                </ScrollView>

                <View style={styles.suggestions}>
                  {suggestions.slice(0, 4).map((s) => (
                    <Chip key={s} onPress={() => sendMessage(s)} style={styles.chip} textStyle={styles.chipText}>
                      {s}
                    </Chip>
                  ))}
                </View>

                <View style={styles.inputRow}>
                  <IconButton icon="microphone" disabled iconColor={luxuryColors.champagneGoldMuted} />
                  <TextInput
                    mode="flat"
                    placeholder={loading ? 'Composing…' : 'Ask anything'}
                    placeholderTextColor={luxuryColors.ivoryMuted}
                    value={message}
                    onChangeText={setMessage}
                    style={styles.input}
                    underlineColor="transparent"
                    activeUnderlineColor="transparent"
                    textColor={luxuryColors.ivory}
                  />
                  <Button mode="contained-tonal" onPress={() => sendMessage(message)} loading={loading} style={styles.send}>
                    Send
                  </Button>
                </View>
              </View>
            </Pressable>
          </KeyboardAvoidingView>
        </Pressable>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 88,
    backgroundColor: luxuryColors.champagneGold,
  },
  dock: {
    position: 'absolute',
    left: 12,
    right: 12,
    bottom: 84,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: luxuryColors.matteBlackSoft,
    borderWidth: 1,
    borderColor: luxuryColors.glassBorder,
  },
  dockInner: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  dockTitle: {
    ...luxuryTypography.display,
    color: luxuryColors.ivory,
    fontSize: 16,
  },
  dockHint: {
    ...luxuryTypography.body,
    color: luxuryColors.ivoryMuted,
    fontSize: 12,
    marginTop: 2,
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(12,10,9,0.72)',
    justifyContent: 'flex-end',
  },
  sheetWrap: {
    maxHeight: '88%',
  },
  sheet: {
    backgroundColor: luxuryColors.matteBlack,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 24,
    borderWidth: 1,
    borderColor: luxuryColors.glassBorder,
  },
  sheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sheetKicker: {
    color: luxuryColors.champagneGold,
    fontSize: 11,
    letterSpacing: 2,
    textTransform: 'uppercase',
  },
  sheetTitle: {
    ...luxuryTypography.display,
    color: luxuryColors.ivory,
    fontSize: 22,
    marginTop: 4,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  langChip: {
    marginRight: 4,
    backgroundColor: luxuryColors.matteBlackSoft,
  },
  messages: {
    maxHeight: 320,
    marginBottom: 12,
  },
  messageLeft: {
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  messageRight: {
    alignItems: 'flex-end',
    marginBottom: 10,
  },
  bubbleLeft: {
    ...luxuryTypography.body,
    backgroundColor: luxuryColors.matteBlackSoft,
    color: luxuryColors.ivory,
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: luxuryColors.glassBorder,
    maxWidth: '92%',
  },
  bubbleRight: {
    ...luxuryTypography.body,
    backgroundColor: luxuryColors.champagneGold,
    color: luxuryColors.matteBlack,
    padding: 12,
    borderRadius: 16,
    maxWidth: '92%',
  },
  suggestions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  chip: {
    backgroundColor: luxuryColors.matteBlackSoft,
    borderColor: luxuryColors.champagneGoldMuted,
    borderWidth: 1,
  },
  chipText: {
    color: luxuryColors.ivory,
    fontSize: 12,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: luxuryColors.matteBlackSoft,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: luxuryColors.glassBorder,
    paddingRight: 4,
  },
  input: {
    flex: 1,
    backgroundColor: 'transparent',
    minHeight: 48,
  },
  send: {
    marginVertical: 4,
  },
});

export default AssistantWidget;
