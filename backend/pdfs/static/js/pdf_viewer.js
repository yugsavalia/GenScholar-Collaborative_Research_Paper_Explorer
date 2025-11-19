pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

(function () {
    const SCALE_STEP = 1.2;
    const MIN_USER_SCALE = 0.5;
    const MAX_USER_SCALE = 3.0;

    let pdfDoc = null;
    let currentPage = 1;
    let currentPdfUrl = null;
    let baseScale = 1;
    let userScale = 1;
    let renderInProgress = false;
    let pendingPage = null;
    let activeAnnotations = [];

    const annotationStore = new Map();

    let canvas;
    let ctx;
    let textLayer;
    let annotationLayer;
    let container;
    let pageNumElement;
    let pageCountElement;
    let pdfLinks = [];

    document.addEventListener('DOMContentLoaded', init);

    function init() {
        container = document.getElementById('pdf-container');
        if (!container || !window.pdfjsLib) {
            return;
        }

        canvas = document.getElementById('pdf-canvas');
        if (!canvas) {
            return;
        }

        ctx = canvas.getContext('2d');
        textLayer = document.getElementById('text-layer');
        annotationLayer = document.getElementById('annotation-layer');
        pageNumElement = document.getElementById('page-num');
        pageCountElement = document.getElementById('page-count');
        pdfLinks = Array.from(document.querySelectorAll('.pdf-link[data-pdf-url]'));

        attachControlHandlers();
        attachPdfLinkHandlers();
        attachSelectionHandlers();
        window.addEventListener('resize', handleResize);

        renderStatusMessage('Select a PDF to view');

        window.loadWorkspacePDF = loadPDF;

        const initialUrl = typeof window.PDF_URL === 'string' && window.PDF_URL.trim() !== '' ? window.PDF_URL : null;
        if (initialUrl) {
            highlightLinkByUrl(initialUrl);
            loadPDF(initialUrl);
        }
    }

    function attachControlHandlers() {
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');
        const zoomInButton = document.getElementById('zoom-in');
        const zoomOutButton = document.getElementById('zoom-out');

        if (prevButton) {
            prevButton.addEventListener('click', goToPreviousPage);
        }
        if (nextButton) {
            nextButton.addEventListener('click', goToNextPage);
        }
        if (zoomInButton) {
            zoomInButton.addEventListener('click', zoomIn);
        }
        if (zoomOutButton) {
            zoomOutButton.addEventListener('click', zoomOut);
        }

        document.addEventListener('keydown', handleKeydown);
    }

    function attachPdfLinkHandlers() {
        pdfLinks.forEach((link) => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const url = link.dataset.pdfUrl;
                if (!url) {
                    return;
                }
                highlightLink(link);
                loadPDF(url);
            });
        });
    }

    function attachSelectionHandlers() {
        if (!textLayer) {
            return;
        }

        textLayer.addEventListener('mouseup', () => {
            const selection = window.getSelection();
            if (!selection || selection.isCollapsed) {
                return;
            }

            const range = selection.getRangeAt(0);
            if (!textLayer.contains(range.commonAncestorContainer)) {
                selection.removeAllRanges();
                return;
            }

            const layerRect = textLayer.getBoundingClientRect();
            const layerWidth = layerRect.width || textLayer.clientWidth;
            const layerHeight = layerRect.height || textLayer.clientHeight;

            if (!layerWidth || !layerHeight) {
                selection.removeAllRanges();
                return;
            }

            const rects = Array.from(range.getClientRects())
                .filter((rect) => rect.width > 0 && rect.height > 0)
                .map((rect) => ({
                    x: (rect.left - layerRect.left) / layerWidth,
                    y: (rect.top - layerRect.top) / layerHeight,
                    width: rect.width / layerWidth,
                    height: rect.height / layerHeight,
                }))
                .filter((rect) => rect.width > 0 && rect.height > 0);

            selection.removeAllRanges();

            if (!rects.length || !pdfDoc || !currentPdfUrl) {
                return;
            }

            activeAnnotations.push({ page: currentPage, rects });
            annotationStore.set(currentPdfUrl, activeAnnotations);
            drawAnnotations();
        });
    }

    async function loadPDF(url) {
        if (!url) {
            renderStatusMessage('No PDF selected.');
            return;
        }

        highlightLinkByUrl(url);

        if (url === currentPdfUrl && pdfDoc) {
            queueRender(currentPage);
            return;
        }

        currentPdfUrl = url;
        renderStatusMessage('Loading PDF…');
        baseScale = 1;
        userScale = 1;
        renderInProgress = false;
        pendingPage = null;

        try {
            const loadingTask = pdfjsLib.getDocument(url);
            pdfDoc = await loadingTask.promise;
            pageCountElement.textContent = pdfDoc.numPages;
            currentPage = 1;
            activeAnnotations = annotationStore.get(url) || [];
            if (!annotationStore.has(url)) {
                annotationStore.set(url, activeAnnotations);
            }
            await renderPage(currentPage);
        } catch (error) {
            console.error('Error loading PDF:', error);
            pdfDoc = null;
            renderStatusMessage('Unable to load PDF.');
        }
    }

    function goToPreviousPage() {
        if (!pdfDoc || currentPage <= 1) {
            return;
        }
        queueRender(currentPage - 1);
    }

    function goToNextPage() {
        if (!pdfDoc || currentPage >= pdfDoc.numPages) {
            return;
        }
        queueRender(currentPage + 1);
    }

    function zoomIn() {
        if (!pdfDoc) {
            return;
        }
        userScale = Math.min(userScale * SCALE_STEP, MAX_USER_SCALE);
        queueRender(currentPage);
    }

    function zoomOut() {
        if (!pdfDoc) {
            return;
        }
        userScale = Math.max(userScale / SCALE_STEP, MIN_USER_SCALE);
        queueRender(currentPage);
    }

    function handleKeydown(event) {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.getAttribute('contenteditable') === 'true')) {
            return;
        }

        if (!pdfDoc) {
            return;
        }

        switch (event.key) {
            case 'ArrowLeft':
            case 'PageUp':
                event.preventDefault();
                goToPreviousPage();
                break;
            case 'ArrowRight':
            case 'PageDown':
                event.preventDefault();
                goToNextPage();
                break;
            case '+':
            case '=':
                if (event.shiftKey || event.key === '+') {
                    event.preventDefault();
                    zoomIn();
                }
                break;
            case '-':
            case '_':
                event.preventDefault();
                zoomOut();
                break;
            default:
                break;
        }
    }

    function queueRender(pageNum) {
        if (renderInProgress) {
            pendingPage = pageNum;
        } else {
            renderPage(pageNum);
        }
    }

    async function renderPage(pageNum) {
        if (!pdfDoc) {
            return;
        }

        renderInProgress = true;

        try {
            const page = await pdfDoc.getPage(pageNum);
            const unscaledViewport = page.getViewport({ scale: 1 });
            const containerWidth = container.clientWidth || 600;
            baseScale = containerWidth / unscaledViewport.width;
            const viewport = page.getViewport({ scale: baseScale * userScale });
            const outputScale = window.devicePixelRatio || 1;

            canvas.width = Math.floor(viewport.width * outputScale);
            canvas.height = Math.floor(viewport.height * outputScale);
            canvas.style.width = `${viewport.width}px`;
            canvas.style.height = `${viewport.height}px`;

            const renderContext = {
                canvasContext: ctx,
                viewport,
                transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null,
            };

            textLayer.innerHTML = '';
            textLayer.style.width = `${viewport.width}px`;
            textLayer.style.height = `${viewport.height}px`;
            annotationLayer.innerHTML = '';
            annotationLayer.style.width = `${viewport.width}px`;
            annotationLayer.style.height = `${viewport.height}px`;
            container.style.height = `${viewport.height}px`;

            await page.render(renderContext).promise;
            await renderTextLayer(page, viewport);

            currentPage = pageNum;
            updatePageInfo();
            drawAnnotations();
        } catch (error) {
            console.error('Error rendering page:', error);
            renderStatusMessage('Unable to render page.');
        } finally {
            renderInProgress = false;
            if (pendingPage !== null) {
                const next = pendingPage;
                pendingPage = null;
                renderPage(next);
            }
        }
    }

    async function renderTextLayer(page, viewport) {
        const textContent = await page.getTextContent();
        pdfjsLib.renderTextLayer({
            textContent,
            container: textLayer,
            viewport,
            textDivs: [],
        });
    }

    function drawAnnotations() {
        annotationLayer.innerHTML = '';

        if (!activeAnnotations.length) {
            return;
        }

        const layerWidth = textLayer.clientWidth;
        const layerHeight = textLayer.clientHeight;

        if (!layerWidth || !layerHeight) {
            return;
        }

        activeAnnotations
            .map((annotation, index) => ({ annotation, index }))
            .filter(({ annotation }) => annotation.page === currentPage)
            .forEach(({ annotation, index }) => {
                annotation.rects.forEach((rect) => {
                    const box = document.createElement('div');
                    box.className = 'annotation-box';
                    box.style.left = `${rect.x * layerWidth}px`;
                    box.style.top = `${rect.y * layerHeight}px`;
                    box.style.width = `${rect.width * layerWidth}px`;
                    box.style.height = `${rect.height * layerHeight}px`;
                    box.addEventListener('dblclick', (event) => {
                        event.stopPropagation();
                        removeAnnotation(index);
                    });
                    annotationLayer.appendChild(box);
                });
            });
    }

    function removeAnnotation(index) {
        if (index < 0 || index >= activeAnnotations.length) {
            return;
        }

        if (!confirm('Remove this highlight?')) {
            return;
        }

        activeAnnotations.splice(index, 1);
        annotationStore.set(currentPdfUrl, activeAnnotations);
        drawAnnotations();
    }

    function updatePageInfo() {
        if (pageNumElement) {
            pageNumElement.textContent = currentPage;
        }
        if (pageCountElement && pdfDoc) {
            pageCountElement.textContent = pdfDoc.numPages;
        }
    }

    function renderStatusMessage(message) {
        if (!ctx || !canvas) {
            return;
        }

        const width = container ? container.clientWidth || 640 : 640;
        const height = 220;

        canvas.width = width;
        canvas.height = height;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        ctx.save();
        ctx.fillStyle = '#f5f5f5';
        ctx.fillRect(0, 0, width, height);
        ctx.fillStyle = '#555';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(message, width / 2, height / 2);
        ctx.restore();

        if (textLayer) {
            textLayer.innerHTML = '';
            textLayer.style.width = `${width}px`;
            textLayer.style.height = `${height}px`;
        }
        if (annotationLayer) {
            annotationLayer.innerHTML = '';
            annotationLayer.style.width = `${width}px`;
            annotationLayer.style.height = `${height}px`;
        }
        if (container) {
            container.style.height = `${height}px`;
        }

        if (pageNumElement) {
            pageNumElement.textContent = '1';
        }
        if (pageCountElement) {
            pageCountElement.textContent = '--';
        }
    }

    function handleResize() {
        if (!pdfDoc) {
            return;
        }
        queueRender(currentPage);
    }

    function highlightLink(link) {
        pdfLinks.forEach((item) => item.classList.remove('active'));
        if (link) {
            link.classList.add('active');
        }
    }

    function highlightLinkByUrl(url) {
        const match = pdfLinks.find((link) => link.dataset.pdfUrl === url);
        if (match) {
            highlightLink(match);
        }
    }
})();

