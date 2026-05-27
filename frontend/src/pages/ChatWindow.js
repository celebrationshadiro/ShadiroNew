import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { io } from 'socket.io-client';
import { Send, User } from 'lucide-react';
import { chats, assistantApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { toast } from '../components/ui/sonner';
import '../styles/ChatWindow.css';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ChatMessage = ({ message, isOwn }) => (
  <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-4`}>
    <div className={`max-w-[70%] ${isOwn ? 'bg-primary text-white' : 'bg-stone-100 text-stone-900'} rounded-2xl px-4 py-3`}>
      {!isOwn && (
        <p className="text-xs font-medium mb-1 opacity-70">{message.sender_name}</p>
      )}
      <p className="text-sm">{message.message}</p>
      <div className={`flex items-center gap-2 mt-1 ${isOwn ? 'text-white/70' : 'text-stone-500'}`}>
        <span className="text-xs">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        {isOwn && message.read && <span className="text-xs">✓✓</span>}
      </div>
    </div>
  </div>
);

const TypingIndicator = ({ userName }) => (
  <div className="flex items-center gap-2 text-stone-500 text-sm mb-4">
    <div className="flex gap-1">
      <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
      <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
      <div className="w-2 h-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
    </div>
    <span>{userName} is typing...</span>
  </div>
);

const ChatWindow = () => {
  const { chatId } = useParams();
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [replyTone, setReplyTone] = useState('formal');
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const loadMessageHistory = useCallback(async () => {
    try {
      const res = await chats.getMessages(chatId);
      setMessages(res.data);
    } catch (error) {
      console.error('Failed to load message history:', error);
    }
  }, [chatId]);


  useEffect(() => {
    if (!user) return;

    // Initialize Socket.IO connection
    const socketInstance = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    socketInstance.on('connect', () => {
      setConnected(true);
      
      // Join the chat room
      socketInstance.emit('join_chat', {
        user_id: user.id,
        chat_id: chatId,
        user_name: user.name,
      });
    });

    socketInstance.on('disconnect', () => {
      setConnected(false);
    });

    socketInstance.on('new_message', (message) => {
      setMessages(prev => [...prev, message]);
      setTyping(null);
    });

    socketInstance.on('user_typing', (data) => {
      if (data.user_id !== user.id) {
        setTyping(data.user_name);
        
        if (typingTimeoutRef.current) {
          clearTimeout(typingTimeoutRef.current);
        }
        
        typingTimeoutRef.current = setTimeout(() => {
          setTyping(null);
        }, 3000);
      }
    });

    socketInstance.on('user_joined', (data) => {
      toast.success(`${data.user_name} joined the chat`);
    });

    socketInstance.on('online_users', (data) => {
      setOnlineUsers(data.user_ids || []);
    });

    socketInstance.on('messages_read', (data) => {
      if (data.reader_id !== user.id) {
        setMessages((prev) =>
          prev.map((m) =>
            m.sender_id === user.id ? { ...m, read: true } : m
          )
        );
      }
    });

    socketInstance.on('error', (error) => {
      console.error('Socket error:', error);
      toast.error(error.message || 'Chat error occurred');
    });

    setSocket(socketInstance);

    // Load message history
    loadMessageHistory();

    // Mark messages as read when viewing
    chats.markRead(chatId).then(() => {
      if (socketInstance && socketInstance.connected) {
        socketInstance.emit('mark_read', { chat_id: chatId, reader_id: user.id });
      }
    }).catch(() => {});

    return () => {
      if (socketInstance) {
        socketInstance.emit('leave_chat', {
          chat_id: chatId,
          user_id: user.id,
        });
        socketInstance.disconnect();
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [chatId, user, loadMessageHistory]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !socket || !connected) return;

    const messageData = {
      chat_id: chatId,
      message: newMessage,
      sender_id: user.id,
      sender_name: user.name,
    };

    // Send via Socket.IO (server persists to DB)
    socket.emit('send_message', messageData);
    setNewMessage('');
  };

  const handleTyping = () => {
    if (socket && connected) {
      socket.emit('typing', {
        chat_id: chatId,
        user_id: user.id,
        user_name: user.name,
      });
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSummarize = async () => {
    setSummaryLoading(true);
    try {
      const res = await assistantApi.summarizeNegotiation({ chat_id: chatId });
      setSummary(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to summarize conversation');
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleSuggestReply = async () => {
    setSuggestionLoading(true);
    try {
      const res = await assistantApi.suggestReply({ chat_id: chatId, tone: replyTone });
      const suggestion = res.data?.suggestions?.[0];
      if (suggestion) {
        setNewMessage(suggestion);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to suggest reply');
    } finally {
      setSuggestionLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-4xl mx-auto w-full px-4 md:px-8 py-8">
        <Card className="h-[calc(100vh-200px)] bg-white rounded-2xl border border-stone-100 flex flex-col">
          {/* Chat Header */}
          <div className="p-6 border-b border-stone-200 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <User size={20} className="text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Chat</h2>
                <p className="text-sm text-stone-500">
                  {connected ? (
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      {onlineUsers.filter((id) => id !== user.id).length > 0 ? 'Online' : 'Connected'}
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-stone-400 rounded-full" />
                      Connecting...
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={handleSummarize} disabled={summaryLoading}>
                {summaryLoading ? 'Summarizing...' : 'Summarize Conversation'}
              </Button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {summary && (
              <div className="mb-6 rounded-2xl bg-stone-50 border border-stone-200 p-4 text-sm text-stone-600">
                <p className="font-medium text-stone-700">Summary</p>
                <p className="mt-1">{summary.summary}</p>
                {summary.key_points?.length ? (
                  <p className="mt-2">Key points: {summary.key_points.join(', ')}</p>
                ) : null}
                {summary.next_steps?.length ? (
                  <p className="mt-2">Next steps: {summary.next_steps.join(', ')}</p>
                ) : null}
              </div>
            )}
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-stone-500">No messages yet. Start the conversation!</p>
              </div>
            ) : (
              <div>
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    isOwn={message.sender_id === user.id}
                  />
                ))}
                {typing && <TypingIndicator userName={typing} />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Message Input */}
          <div className="p-6 border-t border-stone-200">
            <div className="flex items-center gap-3 mb-3">
              <select
                value={replyTone}
                onChange={(e) => setReplyTone(e.target.value)}
                className="border border-stone-200 rounded-full px-3 py-2 text-sm bg-white"
              >
                <option value="formal">Formal</option>
                <option value="quick">Quick</option>
                <option value="concise">Concise</option>
              </select>
              <Button variant="outline" onClick={handleSuggestReply} disabled={suggestionLoading}>
                {suggestionLoading ? 'Generating...' : 'Suggest Reply'}
              </Button>
            </div>
            <div className="flex gap-3">
              <Input
                placeholder="Type your message..."
                className="flex-1 h-12 rounded-full"
                value={newMessage}
                onChange={(e) => {
                  setNewMessage(e.target.value);
                  handleTyping();
                }}
                onKeyPress={handleKeyPress}
                disabled={!connected}
              />
              <Button
                onClick={handleSendMessage}
                className="bg-primary hover:bg-primary/90 h-12 px-6 rounded-full"
                disabled={!newMessage.trim() || !connected}
              >
                <Send size={20} />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ChatWindow;
