import React, { useMemo, useState } from 'react';
import { assistantApi } from '../../lib/api';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Input } from '../ui/input';

const DEFAULT_SUGGESTIONS = [
  'Help me complete onboarding',
  'Suggest next best vendors',
  'Build a booking checklist',
];

const buildContextPayload = (context) => {
  if (!context) return {};
  const payload = { ...context };
  if (context.vendor) {
    payload.profile = context.vendor;
    payload.category_id = context.vendor.category_id || context.category_id;
    payload.vendor_type = context.vendor.vendor_type;
  }
  if (context.event) {
    payload.event = context.event;
  }
  return payload;
};

const AssistantWidget = ({ title = 'Shadiro Assistant', context, role = 'user' }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      from: 'assistant',
      text: 'Hi! I can help you find vendors, compare options, and finish onboarding fast.',
    },
  ]);
  const [suggestions, setSuggestions] = useState(DEFAULT_SUGGESTIONS);

  const payloadBase = useMemo(() => buildContextPayload(context), [context]);

  const handleSend = async (text) => {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, { from: 'user', text: trimmed }]);
    setMessage('');
    setLoading(true);
    try {
      const res = await assistantApi.message({
        message: trimmed,
        role,
        language: 'en',
        ...payloadBase,
      });
      const data = res?.data || {};
      setMessages((prev) => [...prev, { from: 'assistant', text: data.reply || 'Got it. What would you like next?' }]);
      if (Array.isArray(data.suggestions) && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { from: 'assistant', text: 'Sorry, I could not reach the assistant. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <Button
        onClick={() => setOpen((v) => !v)}
        className="rounded-full px-5 py-3 bg-gradient-to-r from-amber-500 via-rose-500 to-fuchsia-600 text-white shadow-xl"
      >
        {open ? 'Close Assistant' : 'Ask Assistant'}
      </Button>

      {open && (
        <Card className="mt-4 w-[340px] sm:w-[380px] bg-white border border-stone-200 shadow-2xl rounded-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-stone-100 bg-gradient-to-r from-stone-50 to-amber-50">
            <p className="text-sm uppercase tracking-wide text-stone-500">AI Vendor Assistant</p>
            <h3 className="text-lg font-semibold text-stone-900">{title}</h3>
          </div>

          <div className="h-72 overflow-y-auto px-5 py-4 space-y-4 bg-white">
            {messages.map((msg, idx) => (
              <div
                key={`${msg.from}-${idx}`}
                className={msg.from === 'assistant' ? 'text-left' : 'text-right'}
              >
                <div
                  className={
                    msg.from === 'assistant'
                      ? 'inline-block rounded-2xl bg-stone-100 px-4 py-2 text-stone-800 text-sm'
                      : 'inline-block rounded-2xl bg-stone-900 px-4 py-2 text-white text-sm'
                  }
                >
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          <div className="px-5 py-3 border-t border-stone-100 bg-stone-50">
            <div className="flex flex-wrap gap-2 mb-3">
              {suggestions.slice(0, 3).map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="text-xs px-3 py-1 rounded-full border border-stone-200 text-stone-700 hover:border-stone-400"
                  type="button"
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={loading ? 'Thinking...' : 'Type your request'}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSend(message);
                  }
                }}
                className="h-10 rounded-full"
              />
              <Button
                onClick={() => handleSend(message)}
                className="rounded-full bg-stone-900 text-white"
                disabled={loading}
              >
                Send
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default AssistantWidget;
