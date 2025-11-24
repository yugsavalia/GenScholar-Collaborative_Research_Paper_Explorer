import InvitationCard from './InvitationCard';

export default function InvitationList({ invitations, onInvitationUpdate, onAccept, onDecline }) {
  if (!invitations || invitations.length === 0) {
    return (
      <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-6 text-center">
        <p className="text-[#BDBDBD]">No pending invitations</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {invitations.map(invitation => (
        <InvitationCard
          key={invitation.id}
          invitation={invitation}
          onAccept={onAccept || onInvitationUpdate}
          onDecline={onDecline || onInvitationUpdate}
        />
      ))}
    </div>
  );
}

