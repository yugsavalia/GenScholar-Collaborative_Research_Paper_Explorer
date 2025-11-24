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
        className="rounded-lg p-6 w-full max-w-[600px] mx-4"
        style={{ background: 'var(--panel-color)', border: '1px solid var(--border-color)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold" style={{ color: 'var(--text-color)' }}>{title}</h2>
          <button
            onClick={onClose}
            className="text-2xl leading-none transition-colors"
            style={{ color: 'var(--muted-text)' }}
            onMouseEnter={(e) => e.target.style.color = 'var(--text-color)'}
            onMouseLeave={(e) => e.target.style.color = 'var(--muted-text)'}
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
