import Icon from './Icon';

export default function SearchBar({ value, onChange, placeholder = 'Search...' }) {
  return (
    <div className="relative w-full">
      <div className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--muted-text)' }}>
        <Icon name="search" size={20} />
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="workspace-search w-full pl-12 pr-4 py-3 rounded-md focus:outline-none"
        style={{
          background: 'var(--input-bg)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-color)'
        }}
        onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
        onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
        data-testid="input-search"
      />
    </div>
  );
}
