export default function Textarea({ 
  label, 
  error, 
  className = '', 
  ...props 
}) {
  return (
    <div className="mb-4">
      {label && (
        <label className="block text-sm font-medium text-[#E0E0E0] mb-2">
          {label}
        </label>
      )}
      <textarea
        className={`w-full px-4 py-2 bg-[#2A2A2A] border border-[#2A2A2A] rounded-md text-[#E0E0E0] placeholder-[#BDBDBD] focus:outline-none focus:border-[#4FC3F7] resize-none ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-[#EF5350]">{error}</p>
      )}
    </div>
  );
}
