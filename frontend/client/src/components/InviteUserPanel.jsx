import { useState } from 'react';
import { inviteUserToWorkspace } from '../api/workspaces';
import Button from './Button';
import Input from './Input';
import Icon from './Icon';

export default function InviteUserPanel({ workspaceId, onInviteSuccess, currentUserRole }) {
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('RESEARCHER'); // Default to RESEARCHER
  const [error, setError] = useState(null);
  const [inviting, setInviting] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleInvite = async (e) => {
    e?.preventDefault();
    
    if (!username.trim()) {
      setError('Please enter a username');
      return;
    }

    setInviting(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      await inviteUserToWorkspace(workspaceId, username.trim(), role);
      setSuccessMessage('Invitation sent');
      setUsername('');
      
      if (onInviteSuccess) {
        onInviteSuccess();
      }
      
      // Clear success message after 2 seconds
      setTimeout(() => setSuccessMessage(null), 2000);
    } catch (err) {
      // Map specific error messages
      const errorMsg = err.message || 'Failed to send invitation';
      if (errorMsg.includes('User does not exist') || errorMsg.includes('not found')) {
        setError('User not found');
      } else if (errorMsg.includes('already a member')) {
        setError('User already a member');
      } else {
        setError(errorMsg);
      }
    } finally {
      setInviting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleInvite(e);
    }
  };

  // Only researchers can invite (or workspace creator)
  const canInvite = currentUserRole === 'RESEARCHER' || currentUserRole === 'CREATOR';
  
  if (!canInvite) {
    return (
      <div className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <p className="text-sm" style={{ color: 'var(--muted-text)' }}>Only researchers can invite users</p>
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
        <span>Invite User</span>
        <Icon 
          name={isExpanded ? "chevron-up" : "chevron-down"} 
          size={16} 
          style={{ color: 'var(--muted-text)' }}
        />
      </button>
      
      <div className={`invite-container ${isExpanded ? 'expanded' : 'collapsed'}`}>
        <form onSubmit={handleInvite} className="space-y-2">
          {error && (
            <div className="p-2 bg-red-500/10 border border-red-500/50 rounded">
              <p className="text-xs text-red-400">{error}</p>
            </div>
          )}
          
          {successMessage && (
            <div className="p-2 bg-green-500/10 border border-green-500/50 rounded">
              <p className="text-xs text-green-400">{successMessage}</p>
            </div>
          )}
          
          <Input
            type="text"
            placeholder="Enter username..."
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
              setError(null); // Clear error when typing
            }}
            onKeyPress={handleKeyPress}
            disabled={inviting}
          />
          
          <div>
            <label className="block text-xs mb-1" style={{ color: 'var(--muted-text)' }}>Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 rounded text-sm"
              style={{
                background: 'var(--input-bg)',
                color: 'var(--text-color)',
                border: '1px solid var(--border-color)'
              }}
              disabled={inviting}
            >
              <option value="RESEARCHER">Researcher</option>
              <option value="REVIEWER">Reviewer</option>
            </select>
          </div>
          
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={inviting || !username.trim()}
          >
            {inviting ? 'Inviting...' : 'Invite'}
          </Button>
        </form>
      </div>
    </div>
  );
}
