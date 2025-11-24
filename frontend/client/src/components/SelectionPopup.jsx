import { useEffect, useRef } from 'react';

/**
 * SelectionPopup - Shows tiny dot above selection for starting chat
 * @param {object} props
 * @param {object} props.position - {x, y} position in viewport coordinates
 * @param {function} props.onStartChat - Callback when dot is clicked
 * @param {function} props.onClose - Callback to close popup
 */
export default function SelectionPopup({ position, onStartChat, onClose }) {
  const buttonRef = useRef(null);

  useEffect(() => {
    // Close popup when clicking outside
    const handleClickOutside = (event) => {
      if (buttonRef.current && !buttonRef.current.contains(event.target)) {
        onClose();
      }
    };

    // Close on Escape key
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onStartChat();
    }
  };

  if (!position) return null;

  // Position is already in viewport coordinates from PdfViewer
  // Position dot above selection (translateY negative)
  return (
    <button
      ref={buttonRef}
      className="pdf-anchor-dot"
      onClick={(e) => {
        e.stopPropagation();
        onStartChat();
      }}
      onKeyDown={handleKeyDown}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
      aria-label="Open thread"
      title="Open thread"
      data-testid="button-start-chat"
    />
  );
}

