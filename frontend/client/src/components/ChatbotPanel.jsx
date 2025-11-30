import { useState, useEffect, useRef } from 'react';
import { storage } from '../utils/storage';
import { STORAGE_KEYS } from '../utils/constants';
import { generateId } from '../utils/ids';
import Icon from './Icon';
import { askChatbot } from '../api/chatbot.js';
import MentionAutocomplete from './MentionAutocomplete';
import { renderMessageWithMentions } from '../utils/mentions.jsx';

export default function ChatbotPanel({ workspaceId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const saved = storage.get(STORAGE_KEYS.BOT(workspaceId)) || [];
    setMessages(saved);
  }, [workspaceId]);

  const shouldAutoScroll = useRef(false);

  useEffect(() => {
    if (shouldAutoScroll.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      shouldAutoScroll.current = false;
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !workspaceId) return;

    const userMessage = {
      id: generateId(),
      role: 'user',
      content: input,
      createdAt: new Date().toISOString()
    };

    const updatedWithUser = [...messages, userMessage];
    setMessages(updatedWithUser);
    storage.set(STORAGE_KEYS.BOT(workspaceId), updatedWithUser);
    shouldAutoScroll.current = true;
    
    const userInput = input;
    setInput('');
    setIsTyping(true);

    try {
      // Call the real API
      const response = await askChatbot(workspaceId, userInput);
      
      // Remove markdown asterisks from the response
      const cleanAnswer = (response.ai_answer || 'Sorry, I could not generate a response.')
        .replace(/\*\*/g, '') // Remove bold markdown (**text**)
        .replace(/\*/g, ''); // Remove any remaining asterisks
      
      const botMessage = {
        id: generateId(),
        role: 'assistant',
        content: cleanAnswer,
        createdAt: new Date().toISOString()
      };

      const updatedWithBot = [...updatedWithUser, botMessage];
      setMessages(updatedWithBot);
      storage.set(STORAGE_KEYS.BOT(workspaceId), updatedWithBot);
      shouldAutoScroll.current = true;
    } catch (error) {
      console.error('Chatbot error:', error);
      // Remove markdown asterisks from error messages too
      const cleanError = (error.message || 'Failed to get response from AI.')
        .replace(/\*\*/g, '')
        .replace(/\*/g, '');
      const errorMessage = {
        id: generateId(),
        role: 'assistant',
        content: `Error: ${cleanError}`,
        createdAt: new Date().toISOString()
      };

      const updatedWithError = [...updatedWithUser, errorMessage];
      setMessages(updatedWithError);
      storage.set(STORAGE_KEYS.BOT(workspaceId), updatedWithError);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            data-testid={`message-bot-${msg.id}`}
          >
            <div
              className="max-w-[80%] px-4 py-2 rounded-lg"
              style={msg.role === 'user'
                ? { background: 'var(--accent-color)', color: '#fff' }
                : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
              }
            >
              <p className="text-sm" style={{ whiteSpace: 'normal', overflowWrap: 'anywhere', wordBreak: 'break-word' }}>{renderMessageWithMentions(msg.content)}</p>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="px-4 py-2 rounded-lg" style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}>
              <p className="text-sm">AI is typing...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSend} className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask the AI assistant..."
              className="w-full px-4 py-2 rounded-md focus:outline-none"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-color)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              data-testid="input-chatbot"
              disabled={isTyping}
            />
            {workspaceId && (
              <MentionAutocomplete
                inputValue={input}
                onInputChange={setInput}
                workspaceId={workspaceId}
                inputRef={inputRef}
              />
            )}
          </div>
          <button
            type="submit"
            disabled={isTyping}
            className="px-4 py-2 rounded-md transition-colors disabled:opacity-50"
            style={{ background: 'var(--accent-color)', color: '#fff' }}
            onMouseEnter={(e) => !isTyping && (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => e.target.style.opacity = '1'}
            data-testid="button-send-chatbot"
          >
            <Icon name="send" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
