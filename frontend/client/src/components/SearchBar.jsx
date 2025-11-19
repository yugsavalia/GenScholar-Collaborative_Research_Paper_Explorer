import Icon from './Icon';

export default function SearchBar({ value, onChange, placeholder = 'Search...' }) {
  return (
    <div className="relative w-full">
      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#BDBDBD]">
        <Icon name="search" size={20} />
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-12 pr-4 py-3 bg-[#1E1E1E] border border-[#2A2A2A] rounded-md text-[#E0E0E0] placeholder-[#BDBDBD] focus:outline-none focus:border-[#4FC3F7]"
        data-testid="input-search"
      />
    </div>
  );
}
