import { useState, useRef, useEffect } from 'react';
import Icon from './Icon';
import MentionAutocomplete from './MentionAutocomplete';
import { renderMessageWithMentions } from '../utils/mentions.jsx';

export default function ThreadItem({ selectionText, messages, onAddMessage, workspaceId }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const shouldAutoScroll = useRef(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (shouldAutoScroll.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      shouldAutoScroll.current = false;
    }
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    onAddMessage(input);
    setInput('');
    shouldAutoScroll.current = true;
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="p-4" style={{ background: 'var(--hover-bg)', borderBottom: '1px solid var(--border-color)' }}>
        <p className="text-xs mb-1" style={{ color: 'var(--muted-text)' }}>Selected text:</p>
        <p className="text-sm italic" style={{ color: 'var(--text-color)' }}>"{selectionText}"</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.author === 'me' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className="max-w-[80%] px-4 py-2 rounded-lg"
              style={msg.author === 'me'
                ? { background: 'var(--accent-color)', color: '#fff' }
                : { background: 'var(--hover-bg)', color: 'var(--text-color)' }
              }
            >
              <p className="text-sm" style={{ whiteSpace: 'normal', overflowWrap: 'anywhere', wordBreak: 'break-word' }}>{renderMessageWithMentions(msg.content)}</p>
            </div>
          </div>
        ))}
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
              placeholder="Reply to thread..."
              className="w-full px-4 py-2 rounded-md focus:outline-none"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-color)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              data-testid="input-thread"
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
            className="px-4 py-2 rounded-md transition-colors"
            style={{ background: 'var(--accent-color)', color: '#fff' }}
            onMouseEnter={(e) => e.target.style.opacity = '0.9'}
            onMouseLeave={(e) => e.target.style.opacity = '1'}
            data-testid="button-send-thread"
          >
            <Icon name="send" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
