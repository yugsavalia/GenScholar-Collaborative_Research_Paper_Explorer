import { useState } from 'react';
import { updateMemberRole } from '../api/workspaces';
import { useAuth } from '../context/AuthContext';
import ConfirmModal from './ConfirmModal';
import Icon from './Icon';

export default function WorkspaceMembersPanel({ 
  members, 
  workspaceId, 
  isCreator, 
  currentUserId,
  onRoleUpdate 
}) {
  const { user } = useAuth();
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, member: null, newRole: null });
  const [updating, setUpdating] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  if (!members || members.length === 0) {
    return (
      <div className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-color)' }}>Members</h3>
        <p className="text-xs" style={{ color: 'var(--muted-text)' }}>No members found</p>
      </div>
    );
  }

  const currentUserMember = members.find(m => m.user.id === currentUserId);
  const otherMembers = members.filter(m => m.user.id !== currentUserId);

  const getRoleDisplayName = (role) => {
    return role === 'RESEARCHER' ? 'Researcher' : 'Reviewer';
  };

  const handleRoleChange = (member, newRole) => {
    // Prevent creator from changing their own role
    if (member.user.id === currentUserId) {
      return;
    }

    setConfirmModal({
      isOpen: true,
      member,
      newRole
    });
  };

  const renderMemberCard = (member) => (
    <div
      key={member.id}
      className="flex items-center justify-between p-2 rounded transition-colors"
      style={{ background: 'var(--hover-bg)' }}
      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--border-color)'}
      onMouseLeave={(e) => e.currentTarget.style.background = 'var(--hover-bg)'}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm truncate" style={{ color: 'var(--text-color)' }}>
            {member.user.username}
          </span>
          {member.is_creator && (
            <span className="text-yellow-400 text-xs" title="Creator">
              ⭐
            </span>
          )}
        </div>
        <div className="text-xs truncate" style={{ color: 'var(--muted-text)' }}>
          {member.user.email}
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        {isCreator && member.user.id !== currentUserId ? (
          <select
            value={member.role}
            onChange={(e) => handleRoleChange(member, e.target.value)}
            className="px-2 py-1 text-xs rounded"
            style={{
              background: 'var(--card-bg)',
              color: 'var(--text-color)',
              border: '1px solid var(--border-color)'
            }}
            disabled={updating}
          >
            <option value="RESEARCHER">Researcher</option>
            <option value="REVIEWER">Reviewer</option>
          </select>
        ) : (
          <span className="px-2 py-1 text-xs rounded" style={{ background: 'var(--card-bg)', color: 'var(--text-color)' }}>
            {getRoleDisplayName(member.role)}
          </span>
        )}
      </div>
    </div>
  );

  const handleConfirmRoleChange = async () => {
    const { member, newRole } = confirmModal;
    setUpdating(true);
    try {
      await updateMemberRole(workspaceId, member.id, newRole);
      if (onRoleUpdate) {
        onRoleUpdate();
      }
    } catch (error) {
      console.error('Failed to update role:', error);
      alert(`Failed to update role: ${error.message}`);
    } finally {
      setUpdating(false);
      setConfirmModal({ isOpen: false, member: null, newRole: null });
    }
  };

  return (
    <>
      <div className="p-4" style={{ borderTop: '1px solid var(--border-color)' }}>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between mb-3 text-sm font-semibold transition-colors"
          style={{ color: 'var(--text-color)' }}
          onMouseEnter={(e) => e.target.style.color = 'var(--accent-color)'}
          onMouseLeave={(e) => e.target.style.color = 'var(--text-color)'}
        >
          <span>Members</span>
          <Icon 
            name={isExpanded ? "chevron-up" : "chevron-down"} 
            size={16} 
            style={{ color: 'var(--muted-text)' }}
          />
        </button>
        
        <div className={`members-list space-y-2 ${isExpanded ? 'expanded' : 'collapsed'}`}>
          {currentUserMember && renderMemberCard(currentUserMember)}
          {otherMembers.map(member => renderMemberCard(member))}
        </div>
      </div>

      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, member: null, newRole: null })}
        onConfirm={handleConfirmRoleChange}
        title="Confirm Role Change"
        message={`Are you sure you want to change ${confirmModal.member?.user.username}'s role from ${getRoleDisplayName(confirmModal.member?.role)} to ${getRoleDisplayName(confirmModal.newRole)}?`}
      />
    </>
  );
}
