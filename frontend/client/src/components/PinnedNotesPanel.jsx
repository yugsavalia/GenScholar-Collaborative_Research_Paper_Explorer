import { useState, useEffect } from 'react';
import { getPinnedNote, savePinnedNote } from '../api/workspaces';
import Button from './Button';
import Icon from './Icon';

export default function PinnedNotesPanel({ workspaceId, currentUserRole }) {
  const [content, setContent] = useState('');
  const [savedContent, setSavedContent] = useState('');
  const [author, setAuthor] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const canEdit = currentUserRole === 'RESEARCHER' || currentUserRole === 'CREATOR';

  useEffect(() => {
    if (workspaceId) {
      fetchPinnedNote();
    }
  }, [workspaceId]);

  const fetchPinnedNote = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPinnedNote(workspaceId);
      setContent(data.content || '');
      setSavedContent(data.content || '');
      setAuthor(data.author);
      setUpdatedAt(data.updated_at);
    } catch (err) {
      console.error('Failed to fetch pinned note:', err);
      setError('Failed to load pinned note');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!canEdit) return;
    
    setSaving(true);
    setError(null);
    try {
      const data = await savePinnedNote(workspaceId, content);
      setSavedContent(data.content);
      setContent(data.content);
      setAuthor(data.author);
      setUpdatedAt(data.updated_at);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to save pinned note:', err);
      setError(err.message || 'Failed to save pinned note');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setContent(savedContent);
    setIsEditing(false);
    setError(null);
  };

  const handleEdit = () => {
    if (canEdit) {
      setIsEditing(true);
    }
  };

  if (loading) {
    return (
      <div className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <p className="text-sm" style={{ color: 'var(--muted-text)' }}>Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between mb-3 text-sm font-semibold transition-colors"
        style={{ color: 'var(--text-color)' }}
        onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
        onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
      >
        <span>Pinned Notes</span>
        <Icon 
          name={isExpanded ? "chevron-up" : "chevron-down"} 
          size={16} 
          style={{ color: 'var(--muted-text)' }}
        />
      </button>
      
      {isExpanded && (
        <div className="pinned-notes-body">
          {error && (
            <div className="p-2 mb-2 bg-red-500/10 border border-red-500/50 rounded">
              <p className="text-xs text-red-400">{error}</p>
            </div>
          )}
          
          {!isEditing ? (
            <div className="pinned-display">
              <div 
                className="pinned-content text-sm mb-2" 
                style={{ 
                  color: 'var(--subtext-color)', 
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}
                onClick={handleEdit}
              >
                {savedContent || 'No pinned notes yet.'}
              </div>
              {(author || updatedAt) && (
                <div className="pinned-meta text-xs" style={{ color: 'var(--muted-text)' }}>
                  {author && <span>By {author.username}</span>}
                  {author && updatedAt && <span> • </span>}
                  {updatedAt && <span>{new Date(updatedAt).toLocaleString()}</span>}
                </div>
              )}
              {canEdit && savedContent && (
                <Button
                  variant="secondary"
                  className="mt-2 w-full"
                  onClick={handleEdit}
                >
                  Edit
                </Button>
              )}
            </div>
          ) : (
            <div className="pinned-editor">
              <textarea
                value={content}
                onChange={(e) => {
                  setContent(e.target.value);
                  setError(null);
                }}
                placeholder="Write pinned notes..."
                rows={6}
                className="w-full px-3 py-2 rounded-md focus:outline-none resize-none"
                style={{
                  background: 'var(--input-bg)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-color)',
                  fontFamily: 'inherit',
                  fontSize: '14px'
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
                maxLength={10000}
              />
              <div className="pinned-actions mt-2 flex gap-2">
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={handleSave}
                  disabled={saving || content === savedContent}
                >
                  {saving ? 'Saving...' : 'Save'}
                </Button>
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={handleCancel}
                  disabled={saving}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
          
          {!isEditing && canEdit && !savedContent && (
            <Button
              variant="primary"
              className="mt-2 w-full"
              onClick={handleEdit}
            >
              Create Note
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

