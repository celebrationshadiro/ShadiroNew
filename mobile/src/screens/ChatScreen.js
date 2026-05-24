import React, { useState, useEffect, useRef } from 'react';
import { View, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { Text, TextInput, IconButton, ActivityIndicator, Button } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { io } from 'socket.io-client';
import { chats, assistant } from '../services/api';

const getSocketUrl = () => {
  const base = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
  return base.replace(/\/api\/?$/, '');
};
const ChatMessage = ({ message, isOwn }) => (
  <View style={[styles.messageContainer, isOwn && styles.ownMessageContainer]}>
    <View style={[styles.messageBubble, isOwn ? styles.ownMessage : styles.otherMessage]}>
      {!isOwn && <Text style={styles.senderName}>{message.sender_name}</Text>}
      <Text style={isOwn ? styles.ownMessageText : styles.messageText}>{message.message}</Text>
      <View style={styles.metaRow}>
        <Text style={isOwn ? styles.ownTimestamp : styles.timestamp}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
        {isOwn && message.status ? (
          <Text style={styles.deliveryStatus}>{message.status}</Text>
        ) : null}
      </View>
    </View>
  </View>
);

const ChatScreen = ({ route }) => {
  const { vendorId } = route.params;
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [remoteTyping, setRemoteTyping] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [replyTone, setReplyTone] = useState('formal');
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const flatListRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    initializeChat();
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  const initializeChat = async () => {
    try {
      // Create or get chat
      const response = await chats.getAll();
      const existingChat = response.data.find(
        (chat) => chat.user_id === user.id && chat.vendor_id === vendorId
      );
      
      const chatIdValue = existingChat ? existingChat.id : `${user.id}_${vendorId}`;
      setChatId(chatIdValue);

      // Load message history
      if (existingChat) {
        const messagesRes = await chats.getMessages(chatIdValue);
        setMessages(messagesRes.data);
      }

      // Initialize Socket.IO
      const socketInstance = io(getSocketUrl(), { transports: ['websocket'] });
      
      socketInstance.on('connect', () => {
        setConnected(true);
        socketInstance.emit('join_chat', {
          user_id: user.id,
          chat_id: chatIdValue,
          user_name: user.name,
        });
      });

      socketInstance.on('disconnect', () => {
        setConnected(false);
      });

      socketInstance.on('reconnect', () => {
        setConnected(true);
      });

      socketInstance.on('new_message', (message) => {
        setMessages((prev) => [...prev, message]);
      });

      socketInstance.on('typing', (payload) => {
        if (payload?.chat_id === chatIdValue && payload?.user_id !== user.id) {
          setRemoteTyping(true);
        }
      });

      socketInstance.on('stop_typing', (payload) => {
        if (payload?.chat_id === chatIdValue && payload?.user_id !== user.id) {
          setRemoteTyping(false);
        }
      });

      setSocket(socketInstance);
    } catch (error) {
      console.error('Failed to initialize chat:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!newMessage.trim() || !socket || !connected) return;

    const tempId = `local_${Date.now()}`;
    const messageData = {
      id: tempId,
      chat_id: chatId,
      message: newMessage,
      sender_id: user.id,
      sender_name: user.name,
      timestamp: new Date().toISOString(),
      status: 'sending',
    };

    setMessages((prev) => [...prev, messageData]);
    socket.emit('send_message', messageData);

    // Save to database
    try {
      const formData = new FormData();
      formData.append('message', newMessage);
      formData.append('sender_id', user.id);
      await chats.sendMessage(chatId, formData);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempId ? { ...msg, status: 'sent' } : msg
        )
      );
    } catch (error) {
      console.error('Failed to save message:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempId ? { ...msg, status: 'failed' } : msg
        )
      );
    }

    setNewMessage('');
    socket.emit('stop_typing', { chat_id: chatId, user_id: user.id });
  };

  const handleTyping = (text) => {
    setNewMessage(text);
    if (!socket || !connected) return;

    socket.emit('typing', { chat_id: chatId, user_id: user.id });
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      socket.emit('stop_typing', { chat_id: chatId, user_id: user.id });
    }, 1200);
  };

  const handleSummarize = async () => {
    if (!chatId) return;
    setSummaryLoading(true);
    try {
      const res = await assistant.summarizeNegotiation({ chat_id: chatId });
      setSummary(res.data);
    } catch (error) {
      console.error('Failed to summarize conversation', error);
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleSuggestReply = async () => {
    if (!chatId) return;
    setSuggestionLoading(true);
    try {
      const res = await assistant.suggestReply({ chat_id: chatId, tone: replyTone });
      const suggestion = res.data?.suggestions?.[0];
      if (suggestion) {
        setNewMessage(suggestion);
      }
    } catch (error) {
      console.error('Failed to suggest reply', error);
    } finally {
      setSuggestionLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#BE185D" />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      <View style={styles.statusBar}>
        <View style={[styles.statusDot, connected && styles.connectedDot]} />
        <Text style={styles.statusText}>{connected ? 'Connected' : 'Connecting...'}</Text>
        <Button
          compact
          mode="text"
          onPress={handleSummarize}
          loading={summaryLoading}
          style={styles.summaryButton}
          labelStyle={styles.summaryLabel}
        >
          Summarize
        </Button>
      </View>

      {summary ? (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Summary</Text>
          <Text style={styles.summaryText}>{summary.summary}</Text>
          {summary.key_points?.length ? (
            <Text style={styles.summaryMeta}>Key points: {summary.key_points.join(', ')}</Text>
          ) : null}
          {summary.next_steps?.length ? (
            <Text style={styles.summaryMeta}>Next steps: {summary.next_steps.join(', ')}</Text>
          ) : null}
        </View>
      ) : null}

      {remoteTyping ? (
        <View style={styles.typingRow}>
          <Text style={styles.typingText}>Vendor is typing...</Text>
        </View>
      ) : null}

      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={({ item }) => (
          <ChatMessage message={item} isOwn={item.sender_id === user.id} />
        )}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messagesList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>Start the conversation!</Text>
          </View>
        }
      />

      <View style={styles.inputContainer}>
        <View style={styles.replyActions}>
          <Button
            compact
            mode={replyTone === 'formal' ? 'contained' : 'outlined'}
            onPress={() => setReplyTone('formal')}
          >
            Formal
          </Button>
          <Button
            compact
            mode={replyTone === 'quick' ? 'contained' : 'outlined'}
            onPress={() => setReplyTone('quick')}
          >
            Quick
          </Button>
          <Button
            compact
            mode={replyTone === 'concise' ? 'contained' : 'outlined'}
            onPress={() => setReplyTone('concise')}
          >
            Concise
          </Button>
          <Button
            compact
            mode="outlined"
            onPress={handleSuggestReply}
            loading={suggestionLoading}
          >
            Suggest
          </Button>
        </View>
        <View style={styles.inputRow}>
          <TextInput
            value={newMessage}
            onChangeText={handleTyping}
            placeholder="Type a message..."
            style={styles.input}
            mode="outlined"
            multiline
          />
          <IconButton
            icon="send"
            size={24}
            iconColor="#fff"
            style={styles.sendButton}
            onPress={handleSend}
            disabled={!newMessage.trim() || !connected}
          />
        </View>
      </View>
    </KeyboardAvoidingView>
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
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#9CA3AF',
    marginRight: 8,
  },
  connectedDot: {
    backgroundColor: '#10B981',
  },
  statusText: {
    fontSize: 12,
    color: '#6B7280',
  },
  summaryButton: {
    marginLeft: 'auto',
  },
  summaryLabel: {
    fontSize: 12,
  },
  summaryCard: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#F8FAFC',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  summaryTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  summaryText: {
    fontSize: 12,
    color: '#4B5563',
    marginTop: 4,
  },
  summaryMeta: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 4,
  },
  typingRow: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F5F5F4',
  },
  typingText: {
    fontSize: 12,
    color: '#78716C',
  },
  messagesList: {
    padding: 15,
  },
  messageContainer: {
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  ownMessageContainer: {
    alignItems: 'flex-end',
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 16,
  },
  otherMessage: {
    backgroundColor: '#F3F4F6',
  },
  ownMessage: {
    backgroundColor: '#BE185D',
  },
  senderName: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
    fontWeight: 'bold',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  messageText: {
    fontSize: 15,
    color: '#1F2937',
  },
  ownMessageText: {
    fontSize: 15,
    color: '#fff',
  },
  timestamp: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 4,
  },
  ownTimestamp: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 4,
  },
  deliveryStatus: {
    fontSize: 11,
    color: '#9CA3AF',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#9CA3AF',
  },
  inputContainer: {
    flexDirection: 'column',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    alignItems: 'flex-end',
  },
  replyActions: {
    width: '100%',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 8,
    alignItems: 'center',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    width: '100%',
  },
  input: {
    flex: 1,
    marginRight: 8,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: '#BE185D',
    margin: 0,
  },
});

export default ChatScreen;
