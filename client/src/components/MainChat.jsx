import { useState, useEffect, useRef } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';
import Icon from './Icon';

export default function MainChat({ workspaceId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const saved = storage.get(STORAGE_KEYS.MAIN_CHAT(workspaceId)) || [];
    setMessages(saved);
  }, [workspaceId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessage = {
      id: generateId(),
      author: 'me',
      content: input,
      createdAt: new Date().toISOString()
    };

    const updated = [...messages, newMessage];
    setMessages(updated);
    storage.set(STORAGE_KEYS.MAIN_CHAT(workspaceId), updated);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.author === 'me' ? 'justify-end' : 'justify-start'}`}
            data-testid={`message-${msg.id}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                msg.author === 'me'
                  ? 'bg-[#4FC3F7] text-white'
                  : 'bg-[#2A2A2A] text-[#E0E0E0]'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSend} className="p-4 border-t border-[#2A2A2A]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 bg-[#2A2A2A] border border-[#2A2A2A] rounded-md text-[#E0E0E0] placeholder-[#BDBDBD] focus:outline-none focus:border-[#4FC3F7]"
            data-testid="input-main-chat"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-[#4FC3F7] text-white rounded-md hover:bg-[#3BA7D1]"
            data-testid="button-send-main-chat"
          >
            <Icon name="send" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
