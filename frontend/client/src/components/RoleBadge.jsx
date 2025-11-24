export default function RoleBadge({ role, isCreator, onClick }) {
  if (!role) return null;

  return (
    <div 
      className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
      onClick={onClick}
      title={onClick ? 'Click to manage members' : ''}
    >
      <span 
        className="px-2 py-1 text-xs font-medium rounded"
        style={{
          background: 'var(--hover-bg)',
          color: 'var(--text-color)',
          border: '1px solid var(--border-color)'
        }}
      >
        {role === 'RESEARCHER' ? 'Researcher' : 'Reviewer'}
      </span>
      {isCreator && (
        <span className="text-yellow-400" title="Workspace Creator">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </span>
      )}
    </div>
  );
}
