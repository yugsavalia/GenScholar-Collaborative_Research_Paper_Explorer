import { useState, useRef, useEffect } from 'react';

const COLOR_PALETTE = [
  { hex: '#FFEB3B', name: 'Yellow' },
  { hex: '#FFB74D', name: 'Orange' },
  { hex: '#F48FB1', name: 'Pink' },
  { hex: '#90CAF9', name: 'Blue' },
  { hex: '#A5D6A7', name: 'Green' },
  { hex: '#BDBDBD', name: 'Grey' }
];

const DEFAULT_COLOR = '#FFEB3B';

if (typeof window !== 'undefined' && !window.currentAnnotationColor) {
  window.currentAnnotationColor = DEFAULT_COLOR;
}

export default function ColorPicker({ onColorChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedColor, setSelectedColor] = useState(() => window.currentAnnotationColor || DEFAULT_COLOR);
  const popoverRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target) &&
          buttonRef.current && !buttonRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleColorSelect = (color) => {
    window.currentAnnotationColor = color.hex;
    setSelectedColor(color.hex);
    setIsOpen(false);
    if (onColorChange) {
      onColorChange(color.hex);
    }
  };

  const currentColor = window.currentAnnotationColor || selectedColor || DEFAULT_COLOR;
  const selectedColorName = COLOR_PALETTE.find(c => c.hex === currentColor)?.name || 'Yellow';

  return (
    <div style={{ position: 'relative' }}>
      <button
        ref={buttonRef}
        id="color-picker-btn"
        className="toolbar-btn color-picker-btn px-4 py-2 rounded flex items-center justify-center transition-colors"
        onClick={() => setIsOpen(!isOpen)}
        style={{ background: 'var(--hover-bg)', color: 'var(--text-color)', minHeight: '100%' }}
        onMouseEnter={(e) => e.target.style.background = 'var(--border-color)'}
        onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
        title="Choose color"
        aria-label={`Selected colour: ${selectedColorName}`}
      >
        <span
          id="color-preview"
          className="color-preview"
          style={{
            background: currentColor,
            width: '18px',
            height: '18px',
            borderRadius: '2px',
            border: '1px solid var(--border-color)',
            display: 'inline-block'
          }}
        />
      </button>
      {isOpen && (
        <div
          ref={popoverRef}
          className="color-picker-popover"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: '4px',
            background: 'var(--panel-color)',
            border: '1px solid var(--border-color)',
            borderRadius: '4px',
            padding: '8px',
            display: 'flex',
            gap: '8px',
            zIndex: 1000,
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}
        >
          {COLOR_PALETTE.map((color) => (
            <button
              key={color.hex}
              onClick={() => handleColorSelect(color)}
              className="color-picker-option"
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '4px',
                background: color.hex,
                border: currentColor === color.hex ? '2px solid var(--accent-color)' : '1px solid var(--border-color)',
                cursor: 'pointer',
                outline: 'none'
              }}
              onFocus={(e) => e.target.style.outline = '2px solid var(--accent-color)'}
              onBlur={(e) => e.target.style.outline = 'none'}
              aria-label={`Select ${color.name}`}
              tabIndex={0}
            />
          ))}
        </div>
      )}
    </div>
  );
}

