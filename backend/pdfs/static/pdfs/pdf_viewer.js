// Set worker path for PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';

let currentPdf = null;
let currentPage = 1;
let pdfPages = 0;
let pageHighlights = {};  // Store highlights for each page
let currentScale = 1.5;   // Default scale

async function loadPDF(url) {
    console.log('Loading PDF from URL:', url);
    try {
        const canvas = document.getElementById('pdf-render');
        const ctx = canvas.getContext('2d');
        
        // Loading indicator
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#333';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Loading PDF...', canvas.width / 2, canvas.height / 2);
        
        console.log('Starting PDF.js loading task...');
        // Load PDF with simple configuration and timeout
        const loadingTask = pdfjsLib.getDocument(url);
        
        // Add timeout to detect if loading hangs
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('PDF loading timeout after 10 seconds')), 10000);
        });
        
        currentPdf = await Promise.race([loadingTask.promise, timeoutPromise]);
        pdfPages = currentPdf.numPages;
        currentPage = 1;
        
        console.log('PDF loaded successfully. Pages:', pdfPages);
        
        // Render first page
        await renderPage(currentPage);
        
        // Update page info
        document.getElementById('page-info').textContent = `Page ${currentPage} of ${pdfPages}`;
        
    } catch (error) {
        console.error('Error loading PDF:', error);
        console.error('Error details:', error.message);
        alert('Failed to load PDF: ' + error.message);
    }
}

async function renderPage(pageNum) {
    if (!currentPdf || pageNum < 1 || pageNum > pdfPages) {
        return;
    }
    
    try {
        const page = await currentPdf.getPage(pageNum);
        
        // Get the canvas and text layer elements
        const canvas = document.getElementById('pdf-render');
        const textLayer = document.getElementById('text-layer');
        
        // Clear text layer
        textLayer.innerHTML = '';
        
        // Set viewport and scale
        const viewport = page.getViewport({ scale: currentScale });
        
        // Set canvas dimensions
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        // Set text layer dimensions
        textLayer.style.height = `${viewport.height}px`;
        textLayer.style.width = `${viewport.width}px`;
        
        // Render PDF page to canvas
        const renderContext = {
            canvasContext: canvas.getContext('2d'),
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        // Get text content and render text layer
        const textContent = await page.getTextContent();
        
        // Render text layer
        pdfjsLib.renderTextLayer({
            textContent: textContent,
            container: textLayer,
            viewport: viewport,
            textDivs: []
        });
        
        // Reapply highlights for this page
        if (pageHighlights[pageNum]) {
            applyHighlights(pageNum);
        }
        
    } catch (error) {
        console.error('Error rendering page:', error);
    }
}

function highlightSelection() {
    const selection = window.getSelection();
    if (!selection.rangeCount) {
        alert('Please select some text first');
        return;
    }
    
    const range = selection.getRangeAt(0);
    const textLayer = document.getElementById('text-layer');
    
    // Check if selection is within text layer
    if (!textLayer.contains(range.commonAncestorContainer)) {
        alert('Please select text within the PDF content');
        return;
    }
    
    // Check if selection is not empty
    if (range.toString().trim() === '') {
        alert('Please select some text to highlight');
        return;
    }
    
    try {
        // Create highlight span
        const highlight = document.createElement('span');
        highlight.className = 'highlight';
        
        // Save highlight data
        if (!pageHighlights[currentPage]) {
            pageHighlights[currentPage] = [];
        }
        
        // Store the highlight information
        const highlightData = {
            text: range.toString(),
            startContainer: getNodeIndex(range.startContainer),
            startOffset: range.startOffset,
            endContainer: getNodeIndex(range.endContainer),
            endOffset: range.endOffset
        };
        
        pageHighlights[currentPage].push(highlightData);
        
        // Apply highlight
        range.surroundContents(highlight);
        selection.removeAllRanges();
        
        console.log(`Highlighted text: "${highlightData.text}"`);
    } catch (error) {
        console.error('Error highlighting selection:', error);
        alert('Error highlighting text. Please try selecting a different range.');
    }
}

function getNodeIndex(node) {
    // Get the index path to this text node within the text layer
    const path = [];
    let current = node;
    const textLayer = document.getElementById('text-layer');
    
    while (current && current !== textLayer) {
        const parent = current.parentNode;
        if (!parent) break;
        
        path.unshift(Array.from(parent.childNodes).indexOf(current));
        current = parent;
    }
    
    return path;
}

function getNodeByIndex(path) {
    // Find a node using its index path
    let current = document.getElementById('text-layer');
    
    for (const index of path) {
        if (!current.childNodes[index]) return null;
        current = current.childNodes[index];
    }
    
    return current;
}

function applyHighlights(pageNum) {
    if (!pageHighlights[pageNum]) return;
    
    const textLayer = document.getElementById('text-layer');
    
    pageHighlights[pageNum].forEach(highlight => {
        try {
            const startNode = getNodeByIndex(highlight.startContainer);
            const endNode = getNodeByIndex(highlight.endContainer);
            
            if (startNode && endNode) {
                const range = document.createRange();
                range.setStart(startNode, highlight.startOffset);
                range.setEnd(endNode, highlight.endOffset);
                
                const highlightSpan = document.createElement('span');
                highlightSpan.className = 'highlight';
                range.surroundContents(highlightSpan);
            }
        } catch (error) {
            console.error('Error applying highlight:', error);
        }
    });
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderPage(currentPage);
        document.getElementById('page-info').textContent = `Page ${currentPage} of ${pdfPages}`;
    }
}

function nextPage() {
    if (currentPage < pdfPages) {
        currentPage++;
        renderPage(currentPage);
        document.getElementById('page-info').textContent = `Page ${currentPage} of ${pdfPages}`;
    }
}

function toggleFallback() {
    const pdfContainer = document.getElementById('pdf-container');
    const fallbackViewer = document.getElementById('fallback-viewer');
    
    if (fallbackViewer.style.display === 'none') {
        pdfContainer.style.display = 'none';
        fallbackViewer.style.display = 'block';
        document.getElementById('fallback-btn').textContent = 'Use PDF.js Viewer';
    } else {
        pdfContainer.style.display = 'block';
        fallbackViewer.style.display = 'none';
        document.getElementById('fallback-btn').textContent = 'Use Simple Viewer';
    }
}

