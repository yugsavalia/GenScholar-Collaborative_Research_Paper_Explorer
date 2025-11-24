import { useEffect, useState } from 'react';
import Icon from './Icon';

/**
 * PdfAnchorIcon - Persistent anchor icon overlay on PDF for threaded discussions
 * @param {object} props
 * @param {number} props.threadId - Thread ID
 * @param {number} props.pageNumber - Page number where anchor is located
 * @param {object} props.anchorRect - Normalized coordinates {x, y, width, height} (0-1)
 * @param {string} props.anchorSide - 'left' or 'right' for icon placement
 * @param {object} props.pageViewportSize - Current page viewport {width, height}
 * @param {number} props.scale - Current PDF scale
 * @param {function} props.onClick - Callback when anchor is clicked
 */
export default function PdfAnchorIcon({
  threadId,
  pageNumber,
  anchorRect,
  anchorSide = 'right',
  pageViewportSize,
  scale,
  onClick,
}) {
  const [position, setPosition] = useState({ left: 0, top: 0 });

  useEffect(() => {
    // Convert normalized coordinates to pixel coordinates
    if (pageViewportSize.width && pageViewportSize.height && anchorRect) {
      const pageWidth = pageViewportSize.width * scale;
      const pageHeight = pageViewportSize.height * scale;

      // Calculate anchor position
      let left, top;
      
      // Icon is 18px, so offset by 10px (half icon + small gap)
      if (anchorSide === 'left') {
        // Place icon to the left of the selection
        left = anchorRect.x * pageWidth - 10;
      } else {
        // Place icon to the right of the selection (default)
        left = (anchorRect.x + anchorRect.width) * pageWidth + 10;
      }

      // Center vertically on the selection
      top = anchorRect.y * pageHeight + (anchorRect.height * pageHeight) / 2;

      setPosition({ left, top });
    }
  }, [anchorRect, anchorSide, pageViewportSize, scale]);

  if (!anchorRect || !pageViewportSize.width) return null;

  return (
    <button
      onClick={onClick}
      className="pdf-anchor-icon absolute pointer-events-auto"
      style={{
        left: `${position.left}px`,
        top: `${position.top}px`,
        transform: 'translate(-50%, -50%)',
      }}
      aria-label="Open thread"
      data-testid={`anchor-icon-thread-${threadId}`}
      title="Open thread"
    >
      <Icon name="message-circle" size={10} className="pdf-anchor-icon-svg" />
    </button>
  );
}

