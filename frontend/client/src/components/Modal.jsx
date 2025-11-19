import { useEffect } from 'react';

export default function Modal({ isOpen, onClose, title, children }) {
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
    }
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div 
        className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-6 w-full max-w-[600px] mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[#E0E0E0]">{title}</h2>
          <button
            onClick={onClose}
            className="text-[#BDBDBD] hover:text-[#E0E0E0] text-2xl leading-none"
            data-testid="button-close-modal"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
