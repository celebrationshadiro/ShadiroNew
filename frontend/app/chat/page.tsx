'use client';

import React, { useState } from 'react';

export default function ChatPage() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages(prev => [...prev, `Me: ${input}`]);
    setInput('');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex-grow w-full flex flex-col">
      <div className="bg-white border border-stone-200 rounded-2xl overflow-hidden shadow-sm max-w-4xl mx-auto w-full flex-grow flex flex-col h-[500px]">
        {/* Header */}
        <div className="bg-stone-900 text-white px-6 py-4 flex items-center justify-between">
          <span className="font-serif text-lg font-bold">Support Desk & Vendor Chat</span>
          <span className="bg-green-600 w-3.5 h-3.5 rounded-full inline-block animate-pulse"></span>
        </div>

        {/* Messaging Logs */}
        <div className="flex-grow p-6 overflow-y-auto space-y-4 bg-stone-50 min-h-[300px]">
          {messages.length === 0 ? (
            <div className="text-center text-stone-400 py-12">
              No messages. Start the conversation with your planner below.
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className="bg-white border border-stone-150 rounded-xl px-4 py-3 max-w-lg shadow-sm">
                <p className="text-stone-800 text-sm">{msg}</p>
              </div>
            ))
          )}
        </div>

        {/* Input Controls */}
        <form onSubmit={handleSend} className="border-t border-stone-200 p-4 bg-white flex items-center space-x-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your message here..."
            className="flex-grow border border-stone-200 rounded-xl px-4 py-3.5 text-sm focus:outline-none focus:border-pink-500 transition"
            aria-label="Chat input message text"
          />
          <button
            type="submit"
            className="bg-pink-600 hover:bg-pink-700 text-white font-bold text-sm px-6 py-3.5 rounded-xl transition shadow-sm"
            aria-label="Send message"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
