export function normalizeRectsToPage(rects, pageRect) {
  if (!pageRect?.width || !pageRect?.height) return [];
  return Array.from(rects).map(r => {
    const x0 = (r.left - pageRect.left) / pageRect.width;
    const y0 = (r.top - pageRect.top) / pageRect.height;
    const x1 = (r.right - pageRect.left) / pageRect.width;
    const y1 = (r.bottom - pageRect.top) / pageRect.height;
    return { x0, y0, x1, y1 };
  });
}

export function denormalizeQuad(quad, pagePixelSize) {
  const { width, height } = pagePixelSize;
  const left = quad.x0 * width;
  const top = quad.y0 * height;
  const right = quad.x1 * width;
  const bottom = quad.y1 * height;
  return { left, top, width: right - left, height: bottom - top };
}

export function rectsIntersect(a, b) {
  const ax1 = a.left, ay1 = a.top, ax2 = a.left + a.width, ay2 = a.top + a.height;
  const bx1 = b.left, by1 = b.top, bx2 = b.left + b.width, by2 = b.top + b.height;
  return ax1 < bx2 && ax2 > bx1 && ay1 < by2 && ay2 > by1;
}

export function hexToRgba(hex, alpha = 1) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) {
    return `rgba(255, 235, 59, ${alpha})`;
  }
  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}


