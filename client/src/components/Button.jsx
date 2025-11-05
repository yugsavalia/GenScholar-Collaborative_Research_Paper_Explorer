export default function Button({ 
  children, 
  onClick, 
  variant = 'primary', 
  type = 'button',
  className = '',
  ...props 
}) {
  const baseStyles = 'px-6 py-2 rounded-md font-medium transition-colors cursor-pointer border';
  
  const variants = {
    primary: 'bg-[#4FC3F7] text-white border-[#4FC3F7] hover:bg-[#3BA7D1]',
    secondary: 'bg-transparent text-[#4FC3F7] border-[#4FC3F7] hover:bg-[#4FC3F7]/10',
    danger: 'bg-[#EF5350] text-white border-[#EF5350] hover:bg-[#D73935]'
  };

  return (
    <button
      type={type}
      onClick={onClick}
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
