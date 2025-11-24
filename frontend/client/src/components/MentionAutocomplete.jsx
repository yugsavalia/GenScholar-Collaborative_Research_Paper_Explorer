import { useState, useEffect, useRef } from 'react';
import { apiGet } from '../api/client';

export default function MentionAutocomplete({ 
  inputValue, 
  onInputChange, 
  onSelectMention, 
  workspaceId,
  inputRef 
}) {
  const [members, setMembers] = useState([]);
  const [filteredMembers, setFilteredMembers] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [mentionStart, setMentionStart] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const suggestionsRef = useRef(null);

  useEffect(() => {
    if (workspaceId) {
      apiGet(`/api/workspaces/${workspaceId}/members/`)
        .then(response => {
          const membersList = response.data.members || [];
          setMembers(membersList.map(m => ({
            id: m.user.id,
            username: m.user.username,
            email: m.user.email
          })));
        })
        .catch(err => console.error('Failed to load members:', err));
    }
  }, [workspaceId]);

  useEffect(() => {
    const cursorPos = inputRef?.current?.selectionStart || inputValue.length;
    const textBeforeCursor = inputValue.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    
    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
      const hasSpace = textAfterAt.includes(' ');
      
      if (!hasSpace) {
        const query = textAfterAt.toLowerCase();
        const filtered = members.filter(m => 
          m.username.toLowerCase().startsWith(query) ||
          m.email.toLowerCase().startsWith(query)
        );
        
        if (filtered.length > 0) {
          setMentionStart(lastAtIndex);
          setFilteredMembers(filtered);
          setShowSuggestions(true);
          setSelectedIndex(0);
          return;
        }
      }
    }
    
    setShowSuggestions(false);
    setMentionStart(null);
  }, [inputValue, members, inputRef]);

  const handleSelect = (member) => {
    if (mentionStart !== null && inputRef?.current) {
      const textBefore = inputValue.substring(0, mentionStart);
      const textAfter = inputValue.substring(inputRef.current.selectionStart);
      const newValue = `${textBefore}@${member.username} ${textAfter}`;
      
      onInputChange(newValue);
      onSelectMention && onSelectMention(member);
      
      setTimeout(() => {
        if (inputRef.current) {
          const newCursorPos = mentionStart + member.username.length + 2;
          inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
          inputRef.current.focus();
        }
      }, 0);
    }
    
    setShowSuggestions(false);
    setMentionStart(null);
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions) return;
    
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => 
        prev < filteredMembers.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => prev > 0 ? prev - 1 : 0);
    } else if (e.key === 'Enter' && filteredMembers.length > 0) {
      e.preventDefault();
      handleSelect(filteredMembers[selectedIndex]);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  useEffect(() => {
    const input = inputRef?.current;
    if (input && showSuggestions) {
      const handler = (e) => handleKeyDown(e);
      input.addEventListener('keydown', handler);
      return () => {
        input.removeEventListener('keydown', handler);
      };
    }
  }, [showSuggestions, filteredMembers, selectedIndex, mentionStart, inputValue]);

  if (!showSuggestions || filteredMembers.length === 0) {
    return null;
  }

  return (
    <div
      ref={suggestionsRef}
      className="absolute z-50 rounded-md shadow-lg max-h-48 overflow-y-auto"
      style={{
        background: 'var(--panel-color)',
        border: '1px solid var(--border-color)',
        bottom: '100%',
        marginBottom: '4px',
        minWidth: '200px'
      }}
    >
      {filteredMembers.map((member, index) => (
        <div
          key={member.id}
          className="px-3 py-2 cursor-pointer transition-colors"
          style={{
            background: index === selectedIndex ? 'var(--hover-bg)' : 'transparent',
            color: 'var(--text-color)'
          }}
          onMouseEnter={() => setSelectedIndex(index)}
          onClick={() => handleSelect(member)}
        >
          <div className="font-medium">@{member.username}</div>
          <div className="text-xs" style={{ color: 'var(--muted-text)' }}>
            {member.email}
          </div>
        </div>
      ))}
    </div>
  );
}

