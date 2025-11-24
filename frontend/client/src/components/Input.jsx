export default function Input({ 
  label, 
  error, 
  className = '', 
  ...props 
}) {
  return (
    <div className="mb-4">
      {label && (
        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-color)' }}>
          {label}
        </label>
      )}
      <input
        className={`w-full px-4 py-2 rounded-md focus:outline-none ${className}`}
        style={{
          background: 'var(--input-bg)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-color)'
        }}
        onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
        onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm" style={{ color: '#EF5350' }}>{error}</p>
      )}
    </div>
  );
}
