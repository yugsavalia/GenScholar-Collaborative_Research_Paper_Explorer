import { useState } from 'react';
import Button from './Button';

export default function InvitationCard({ invitation, onAccept, onDecline }) {
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleAccept = async () => {
    setProcessing(true);
    setError(null);
    try {
      if (onAccept) {
        await onAccept(invitation.id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleDecline = async () => {
    setProcessing(true);
    setError(null);
    try {
      if (onDecline) {
        await onDecline(invitation.id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const getRoleDisplayName = (role) => {
    return role === 'RESEARCHER' ? 'Researcher' : 'Reviewer';
  };

  return (
    <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4 hover:border-[#4FC3F7] transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-[#E0E0E0] mb-1">
            {invitation.workspace.name}
          </h3>
          <p className="text-sm text-[#BDBDBD]">
            Invited by <span className="text-[#4FC3F7]">{invitation.invited_by.username}</span> as{' '}
            <span className="text-[#4FC3F7]">{getRoleDisplayName(invitation.role)}</span>
          </p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-400 mb-2">{error}</p>
      )}

      <div className="flex gap-2">
        <Button
          onClick={handleAccept}
          variant="primary"
          className="flex-1"
          disabled={processing}
        >
          {processing ? 'Processing...' : 'Accept'}
        </Button>
        <Button
          onClick={handleDecline}
          variant="secondary"
          className="flex-1"
          disabled={processing}
        >
          Decline
        </Button>
      </div>
    </div>
  );
}

