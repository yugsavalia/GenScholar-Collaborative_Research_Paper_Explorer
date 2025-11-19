import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function PdfViewer({ url, onPageChange, annotations = [], onTextSelect }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection.toString();
    
    if (text && onTextSelect) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      
      onTextSelect({
        text,
        pageNumber,
        rects: [{
          x: rect.x,
          y: rect.y,
          w: rect.width,
          h: rect.height
        }]
      });
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-4 bg-[#1E1E1E] border-b border-[#2A2A2A]">
        <div className="flex gap-2">
          <button
            onClick={() => setPageNumber(prev => Math.max(1, prev - 1))}
            disabled={pageNumber <= 1}
            className="px-3 py-1 bg-[#2A2A2A] text-[#E0E0E0] rounded disabled:opacity-50"
            data-testid="button-prev-page"
          >
            Previous
          </button>
          <span className="px-4 py-1 text-[#E0E0E0]">
            Page {pageNumber} of {numPages || '?'}
          </span>
          <button
            onClick={() => setPageNumber(prev => Math.min(numPages, prev + 1))}
            disabled={pageNumber >= numPages}
            className="px-3 py-1 bg-[#2A2A2A] text-[#E0E0E0] rounded disabled:opacity-50"
            data-testid="button-next-page"
          >
            Next
          </button>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setScale(s => Math.max(0.5, s - 0.1))}
            className="px-3 py-1 bg-[#2A2A2A] text-[#E0E0E0] rounded"
            data-testid="button-zoom-out"
          >
            -
          </button>
          <span className="px-4 py-1 text-[#E0E0E0]">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale(s => Math.min(2.0, s + 0.1))}
            className="px-3 py-1 bg-[#2A2A2A] text-[#E0E0E0] rounded"
            data-testid="button-zoom-in"
          >
            +
          </button>
        </div>
      </div>
      
      <div 
        className="flex-1 overflow-auto bg-[#121212] p-4"
        onMouseUp={handleTextSelection}
      >
        <div className="flex justify-center">
          <Document
            file={url}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={<div className="text-[#BDBDBD]">Loading PDF...</div>}
            error={<div className="text-[#EF5350]">Error loading PDF</div>}
          >
            <Page 
              pageNumber={pageNumber} 
              scale={scale}
              renderTextLayer={true}
              renderAnnotationLayer={false}
            />
          </Document>
        </div>
      </div>
    </div>
  );
}
