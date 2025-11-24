import { hexToRgba } from '../utils/annotations';

export default function AnnotationOverlay({ annotations = [], pagePixelSize, typeColors }) {
	return (
		<div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
			{annotations.map(a =>
				(a.quads || []).map((q, idx) => {

					const rect = {
						left: q.left ?? 0,
						top: q.top ?? 0,
						width: q.width ?? 0,
						height: q.height ?? 0
					};
					
					// Skip invalid rects
					if (rect.width <= 0 || rect.height <= 0) {
						return null;
					}
					
					const common = {
						position: 'absolute',
						left: `${rect.left}px`,
						top: `${rect.top}px`,
						width: `${rect.width}px`,
						height: `${rect.height}px`,
						pointerEvents: 'none',
						zIndex: 20
					};
					
					const type = (a.type || '').toUpperCase();
					const annotationColor = a.color || '#FFEB3B';
					
					if (type === 'HIGHLIGHT') {
						return (
							<div
								key={`${a.id}-${idx}`}
								className="annotation highlight"
								style={{
									...common,
									pointerEvents: 'none',
									mixBlendMode: 'multiply',
									background: hexToRgba(annotationColor, 0.5),
									zIndex: 1
								}}
							/>
						);
					}
					if (type === 'UNDERLINE') {
						const underlineHeight = Math.max(2, Math.round(rect.height * 0.15));
						return (
							<div
								key={`${a.id}-${idx}`}
								className="annotation underline"
								style={{
									...common,
									height: `${underlineHeight}px`,
									top: `${rect.top + rect.height - underlineHeight}px`,
									background: annotationColor
								}}
							/>
						);
					}
					return null;
				})
			)}
		</div>
	);
}


