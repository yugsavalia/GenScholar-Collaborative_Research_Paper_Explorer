import { useState, useRef, useCallback, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import AnnotationOverlay from './AnnotationOverlay';
import SelectionPopup from './SelectionPopup';
import PdfAnchorIcon from './PdfAnchorIcon';
import { normalizeRectsToPage, denormalizeQuad } from '../utils/annotations';

export default function PdfViewer({ 
	url, 
	onPageChange, 
	annotations = [], 
	onTextSelect,
	threads = [], // Array of thread objects with anchor_rect, page_number, etc.
	onStartChat, // Callback when "Start chat" is clicked: (selectionData) => void
	onAnchorClick, // Callback when anchor icon is clicked: (threadId) => void
	annotationMode = 'SELECT' // Current annotation mode - only show popup in SELECT mode
}) {
	const [numPages, setNumPages] = useState(null);
	const [pageNumber, setPageNumber] = useState(1);
	const [scale, setScale] = useState(1.0);
	const [maxScale, setMaxScale] = useState(null);
	const [pageViewportSize, setPageViewportSize] = useState({ width: 0, height: 0 });
	const [selectionPopup, setSelectionPopup] = useState(null); // {x, y, selectionData}
	const [isEditingPageNumber, setIsEditingPageNumber] = useState(false);
	const [pageInputValue, setPageInputValue] = useState('');
	const containerRef = useRef(null);
	const pageWrapperRef = useRef(null);
	const pageInputRef = useRef(null);

	const onDocumentLoadSuccess = ({ numPages }) => {
		setNumPages(numPages);
	};

	const calculateFitScale = useCallback(() => {
		if (!containerRef.current || !pageViewportSize.width) return null;
		const padding = 32;
		const available = containerRef.current.clientWidth - padding;
		if (available > 0) {
			const fitScale = available / pageViewportSize.width;
			return Math.max(0.25, Math.min(3, fitScale));
		}
		return null;
	}, [pageViewportSize.width]);

	const fitToWidth = useCallback(() => {
		const fitScale = calculateFitScale();
		if (fitScale !== null) {
			setMaxScale(fitScale);
			setScale(fitScale);
		}
	}, [calculateFitScale]);

	const handleTextSelection = () => {
		const selection = window.getSelection();
		if (!selection || selection.rangeCount === 0) {
			setSelectionPopup(null);
			return;
		}
		
		const text = selection.toString().trim();
		if (!text) {
			setSelectionPopup(null);
			return;
		}
		
		const range = selection.getRangeAt(0);
		
		// Verify selection is within the PDF text layer
		const textLayer = pageWrapperRef.current?.querySelector('.react-pdf__Page__textContent.textLayer');
		if (!textLayer || !textLayer.contains(range.commonAncestorContainer)) {
			setSelectionPopup(null);
			return;
		}
		
		// Get precise rects for the selected range (one per contiguous text piece)
		// getClientRects() returns one rect per line/contiguous piece of selected text
		const rects = Array.from(range.getClientRects()).filter(r => 
			r.width > 0 && r.height > 0
		);
		
		if (rects.length === 0) {
			setSelectionPopup(null);
			return;
		}
		
		// Use the page wrapper rect as the reference frame for normalization
		// This ensures coordinates are relative to the page container, which matches
		// the coordinate system used for rendering overlays
		const pageRect = pageWrapperRef.current?.getBoundingClientRect();
		if (!pageRect || !pageRect.width || !pageRect.height) {
			return;
		}
		
		// Normalize each rect to page coordinates (0-1 range)
		// Each rect from getClientRects() becomes one quad in the stored annotation
		const quads = normalizeRectsToPage(rects, pageRect);
		
		if (quads.length === 0) {
			return;
		}
		
		// Only show popup in SELECT mode (lowercase 'select')
		if (annotationMode === 'select' && onStartChat) {
			const containerRect = containerRef.current?.getBoundingClientRect();
			if (containerRect) {
				// Get the first rect for popup position
				const firstRect = rects[0];
				
				// Calculate anchor_rect from quads (bounding box)
				const anchorRect = {
					x: Math.min(...quads.map(q => q.x0)),
					y: Math.min(...quads.map(q => q.y0)),
					width: Math.max(...quads.map(q => q.x1)) - Math.min(...quads.map(q => q.x0)),
					height: Math.max(...quads.map(q => q.y1)) - Math.min(...quads.map(q => q.y0)),
				};
				
				// Calculate popup position in viewport coordinates (for fixed positioning)
				const popupX = firstRect.left + firstRect.width / 2;
				const popupY = firstRect.top;
				
				// Show popup at selection position
				setSelectionPopup({
					x: popupX,
					y: popupY,
					selectionData: {
						text,
						pageNumber,
						anchorRect,
						quads
					}
				});
			}
		} else if (onTextSelect) {
			// Annotation flow - pass normalized quads (one per selected rect)
			onTextSelect({
				text,
				pageNumber,
				quads
			});
		}
	};
	
	const handleStartChat = () => {
		if (selectionPopup && onStartChat) {
			onStartChat(selectionPopup.selectionData);
			setSelectionPopup(null);
			// Clear selection
			window.getSelection().removeAllRanges();
		}
	};

	// No longer needed - using overlay-based rendering instead of inline classes

	// Configure PDF links to open in new tabs
	useEffect(() => {
		const configureLinks = () => {
			const annotationLayer = pageWrapperRef.current?.querySelector('.react-pdf__Page__annotations');
			if (annotationLayer) {
				const links = annotationLayer.querySelectorAll('a');
				links.forEach(link => {
					link.target = '_blank';
					link.rel = 'noopener noreferrer';
				});
			}
		};
		
		// Run after a short delay to ensure annotation layer is rendered
		const timeoutId = setTimeout(configureLinks, 200);
		return () => clearTimeout(timeoutId);
	}, [pageNumber, scale, url]);

	// Calculate and set maxScale on initial PDF load and when container/page size changes
	useEffect(() => {
		if (pageViewportSize.width && containerRef.current) {
			const fitScale = calculateFitScale();
			if (fitScale !== null) {
				setMaxScale(fitScale);
			}
		}
	}, [pageViewportSize.width, calculateFitScale]);

	// Recalculate maxScale on window resize
	useEffect(() => {
		const handleResize = () => {
			if (pageViewportSize.width && containerRef.current) {
				const fitScale = calculateFitScale();
				if (fitScale !== null) {
					setMaxScale(fitScale);
					if (scale > fitScale) {
						setScale(fitScale);
					}
				}
			}
		};

		window.addEventListener('resize', handleResize);
		return () => window.removeEventListener('resize', handleResize);
	}, [pageViewportSize.width, scale, calculateFitScale]);

	// Clamp scale to maxScale when maxScale changes or scale exceeds it
	useEffect(() => {
		if (maxScale !== null && scale > maxScale) {
			setScale(maxScale);
		}
	}, [maxScale, scale]);

	const handlePageNumberClick = () => {
		if (numPages) {
			setPageInputValue(pageNumber.toString());
			setIsEditingPageNumber(true);
		}
	};

	const handlePageInputKeyDown = (e) => {
		if (e.key === 'Enter') {
			const inputValue = e.target.value.trim();
			const parsedPage = parseInt(inputValue, 10);
			
			if (!isNaN(parsedPage) && parsedPage >= 1 && parsedPage <= numPages) {
				setPageNumber(parsedPage);
				if (onPageChange) {
					onPageChange(parsedPage);
				}
			}
			setIsEditingPageNumber(false);
		} else if (e.key === 'Escape') {
			setIsEditingPageNumber(false);
		}
	};

	const handlePageInputBlur = () => {
		setIsEditingPageNumber(false);
	};

	useEffect(() => {
		if (isEditingPageNumber && pageInputRef.current) {
			pageInputRef.current.focus();
			pageInputRef.current.select();
		}
	}, [isEditingPageNumber]);

	return (
		<div className="flex flex-col h-full min-h-0">
			<div className="flex justify-between items-center p-4 flex-shrink-0" style={{ background: 'var(--panel-color)', borderBottom: '1px solid var(--border-color)' }}>
				<div className="flex gap-2">
					<button
						onClick={() => setPageNumber(prev => Math.max(1, prev - 1))}
						disabled={pageNumber <= 1}
						className="px-3 py-1 rounded disabled:opacity-50 transition-colors"
						style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}
						onMouseEnter={(e) => !e.target.disabled && (e.target.style.background = 'var(--border-color)')}
						onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
						data-testid="button-prev-page"
					>
						Previous
					</button>
					{isEditingPageNumber ? (
						<input
							ref={pageInputRef}
							type="text"
							value={pageInputValue}
							onChange={(e) => {
								const value = e.target.value.replace(/\D/g, '');
								setPageInputValue(value);
							}}
							onKeyDown={handlePageInputKeyDown}
							onBlur={handlePageInputBlur}
							className="px-2 py-1 rounded"
							style={{
								width: '60px',
								background: 'var(--input-bg)',
								color: 'var(--text-color)',
								border: '1px solid var(--border-color)',
								textAlign: 'center',
								fontSize: 'inherit'
							}}
						/>
					) : (
						<span 
							className="px-4 py-1 cursor-pointer" 
							style={{ color: 'var(--text-color)' }}
							onClick={handlePageNumberClick}
						>
							Page {pageNumber} of {numPages || '?'}
						</span>
					)}
					<button
						onClick={() => setPageNumber(prev => Math.min(numPages, prev + 1))}
						disabled={pageNumber >= numPages}
						className="px-3 py-1 rounded disabled:opacity-50 transition-colors"
						style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}
						onMouseEnter={(e) => !e.target.disabled && (e.target.style.background = 'var(--border-color)')}
						onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
						data-testid="button-next-page"
					>
						Next
					</button>
				</div>
				<div className="flex gap-2">
					<button
						onClick={() => setScale(s => {
							const newScale = Math.max(0.5, s - 0.1);
							return maxScale !== null ? Math.min(maxScale, newScale) : newScale;
						})}
						className="px-3 py-1 rounded transition-colors"
						style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}
						onMouseEnter={(e) => e.target.style.background = 'var(--border-color)'}
						onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
						data-testid="button-zoom-out"
					>
						-
					</button>
					<span className="px-4 py-1" style={{ color: 'var(--text-color)' }}>{Math.round(scale * 100)}%</span>
					<button
						onClick={() => {
							if (maxScale !== null && scale >= maxScale) return;
							const newScale = scale + 0.1;
							if (maxScale !== null && newScale > maxScale) {
								setScale(maxScale);
							} else {
								setScale(newScale);
							}
						}}
						disabled={maxScale !== null && scale >= maxScale}
						className={`px-3 py-1 rounded transition-colors ${maxScale !== null && scale >= maxScale ? 'opacity-40 cursor-not-allowed' : ''}`}
						style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}
						onMouseEnter={(e) => !e.target.disabled && (e.target.style.background = 'var(--border-color)')}
						onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
						data-testid="button-zoom-in"
					>
						+
					</button>
					<button
						onClick={fitToWidth}
						className="px-3 py-1 rounded transition-colors"
						style={{ background: 'var(--hover-bg)', color: 'var(--text-color)' }}
						onMouseEnter={(e) => e.target.style.background = 'var(--border-color)'}
						onMouseLeave={(e) => e.target.style.background = 'var(--hover-bg)'}
						data-testid="button-fit-width"
					>
						Fit
					</button>
				</div>
			</div>
			
			<div
				ref={containerRef}
				className="flex-1 overflow-auto p-4 relative min-h-0"
				style={{ background: 'var(--bg-color)' }}
				onMouseUp={handleTextSelection}
			>
				<div className="flex justify-center relative">
					<div className="relative" ref={pageWrapperRef}>
						<Document
							file={url}
							onLoadSuccess={onDocumentLoadSuccess}
							loading={<div style={{ color: 'var(--muted-text)' }}>Loading PDF...</div>}
							error={<div style={{ color: '#EF5350' }}>Error loading PDF</div>}
						>
							<Page
								pageNumber={pageNumber}
								scale={scale}
								renderTextLayer={true}
								renderAnnotationLayer={true}
								onLoadSuccess={(page) => {
									const viewport = page.getViewport({ scale: 1.0 });
									setPageViewportSize({ width: viewport.width, height: viewport.height });
								}}
								onRenderSuccess={() => {
									// Configure links to open in new tabs
									setTimeout(() => {
										const annotationLayer = pageWrapperRef.current?.querySelector('.react-pdf__Page__annotations');
										if (annotationLayer) {
											const links = annotationLayer.querySelectorAll('a');
											links.forEach(link => {
												link.target = '_blank';
												link.rel = 'noopener noreferrer';
											});
										}
									}, 100);
								}}
							/>
						</Document>
						<div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
							{/* Render all annotations (including highlights/underlines) using overlay */}
							<AnnotationOverlay
								annotations={(annotations || [])
									.filter(a => (a.page_number || a.pageNumber) === pageNumber)
									.map(a => {
										const viewport = { width: pageViewportSize.width * scale, height: pageViewportSize.height * scale };
										// Convert normalized quads to pixel coordinates for rendering
										const mapped = (a.quads || []).map(q => {
											const abs = denormalizeQuad(q, viewport);
											return { ...abs };
										});
										return { ...a, quads: mapped };
									})}
								pagePixelSize={{ width: pageViewportSize.width * scale, height: pageViewportSize.height * scale }}
							/>
							
							{/* Render anchor icons for threads on current page */}
							{threads
								.filter(thread => thread.page_number === pageNumber)
								.map(thread => (
									<PdfAnchorIcon
										key={thread.id}
										threadId={thread.id}
										pageNumber={thread.page_number}
										anchorRect={thread.anchor_rect}
										anchorSide={thread.anchor_side || 'right'}
										pageViewportSize={pageViewportSize}
										scale={scale}
										onClick={() => onAnchorClick && onAnchorClick(thread.id)}
									/>
								))}
						</div>
						
						{/* Selection popup - positioned relative to container */}
						{selectionPopup && (
							<SelectionPopup
								position={{ x: selectionPopup.x, y: selectionPopup.y }}
								onStartChat={handleStartChat}
								onClose={() => setSelectionPopup(null)}
							/>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
