import { useState, useEffect, useRef } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';
import Icon from './Icon';

export default function ChatbotPanel({ workspaceId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const saved = storage.get(STORAGE_KEYS.BOT(workspaceId)) || [];
    setMessages(saved);
  }, [workspaceId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      id: generateId(),
      role: 'user',
      content: input,
      createdAt: new Date().toISOString()
    };

    const updatedWithUser = [...messages, userMessage];
    setMessages(updatedWithUser);
    storage.set(STORAGE_KEYS.BOT(workspaceId), updatedWithUser);
    
    const userInput = input;
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const botMessage = {
        id: generateId(),
        role: 'assistant',
        content: `AI: I received your message "${userInput}". This is a mock response.`,
        createdAt: new Date().toISOString()
      };

      const updatedWithBot = [...updatedWithUser, botMessage];
      setMessages(updatedWithBot);
      storage.set(STORAGE_KEYS.BOT(workspaceId), updatedWithBot);
      setIsTyping(false);
    }, 400);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            data-testid={`message-bot-${msg.id}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-[#4FC3F7] text-white'
                  : 'bg-[#2A2A2A] text-[#E0E0E0]'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-[#2A2A2A] text-[#E0E0E0] px-4 py-2 rounded-lg">
              <p className="text-sm">AI is typing...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSend} className="p-4 border-t border-[#2A2A2A]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI assistant..."
            className="flex-1 px-4 py-2 bg-[#2A2A2A] border border-[#2A2A2A] rounded-md text-[#E0E0E0] placeholder-[#BDBDBD] focus:outline-none focus:border-[#4FC3F7]"
            data-testid="input-chatbot"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={isTyping}
            className="px-4 py-2 bg-[#4FC3F7] text-white rounded-md hover:bg-[#3BA7D1] disabled:opacity-50"
            data-testid="button-send-chatbot"
          >
            <Icon name="send" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
