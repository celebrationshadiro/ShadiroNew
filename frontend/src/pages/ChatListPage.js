import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/ui/card';
import { MessageSquare, User } from 'lucide-react';
import { chats } from '../lib/api';

const ChatListItem = ({ chat, onClick }) => {
  return (
    <Card
      className="p-4 bg-white rounded-xl border border-stone-100 hover:shadow-md transition-all cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
          <User size={20} className="text-primary" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium">Chat #{chat.id.slice(0, 8)}</h3>
          {chat.last_message && (
            <p className="text-sm text-stone-500 truncate">{chat.last_message}</p>
          )}
          {chat.last_message_at && (
            <p className="text-xs text-stone-400">
              {new Date(chat.last_message_at).toLocaleDateString()}
            </p>
          )}
        </div>
        <MessageSquare size={20} className="text-stone-400" />
      </div>
    </Card>
  );
};

const ChatListPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    loadChats();
  }, [user]);

  const loadChats = async () => {
    setLoading(true);
    try {
      const res = await chats.getAll();
      setChats(res.data);
    } catch (error) {
      console.error('Failed to load chats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500 text-lg">Loading chats...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-4xl mx-auto w-full px-4 md:px-8 py-8">
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight mb-8 font-heading">
          My Chats
        </h1>

        {chats.length === 0 ? (
          <Card className="p-12 text-center bg-white rounded-2xl">
            <MessageSquare className="mx-auto mb-4 text-stone-300" size={48} />
            <p className="text-stone-500">No chats yet</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {chats.map((chat) => (
              <ChatListItem
                key={chat.id}
                chat={chat}
                onClick={() => navigate(`/chat/${chat.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatListPage;
