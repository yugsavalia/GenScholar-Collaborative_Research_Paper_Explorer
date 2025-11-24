document.addEventListener('DOMContentLoaded', () => {
    if (typeof pdfjsLib === 'undefined') {
        console.error('pdfjsLib is not available. Make sure PDF.js is loaded before annotator.js');
        return;
    }

    const pdfContainer = document.getElementById('pdf-container');
    if (!pdfContainer) {
        return;
    }

    const state = {
        pdfDoc: null,
        pdfUrl: null,
        pdfId: null,
        currentPage: 1,
        totalPages: 0,
        scale: 1.2,
        annotationsByPage: new Map(),
        annotationApiBase: null,
    };

    const controls = document.createElement('div');
    controls.className = 'pdf-controls';

    const prevButton = document.createElement('button');
    prevButton.textContent = 'Previous Page';
    prevButton.addEventListener('click', () => changePage(-1));

    const pageInfo = document.createElement('span');
    pageInfo.id = 'page-info';
    pageInfo.textContent = 'No PDF loaded';

    const nextButton = document.createElement('button');
    nextButton.textContent = 'Next Page';
    nextButton.addEventListener('click', () => changePage(1));

    controls.append(prevButton, pageInfo, nextButton);

    const stage = document.createElement('div');
    stage.className = 'pdf-stage';

    const canvas = document.createElement('canvas');
    canvas.id = 'pdf-canvas';
    const ctx = canvas.getContext('2d');

    const textLayer = document.createElement('div');
    textLayer.id = 'text-layer';

    const annotationLayer = document.createElement('div');
    annotationLayer.id = 'annotation-layer';

    stage.append(canvas, textLayer, annotationLayer);
    pdfContainer.append(controls, stage);

    prevButton.disabled = true;
    nextButton.disabled = true;

    textLayer.addEventListener('mouseup', handleSelection);
    bindPdfLinks();

    function changePage(delta) {
        if (!state.pdfDoc) return;
        const target = state.currentPage + delta;
        if (target < 1 || target > state.totalPages) return;
        renderPage(target);
    }

    async function loadDocument() {
        if (!state.pdfUrl) return;
        try {
            pageInfo.textContent = 'Loading…';
            prevButton.disabled = true;
            nextButton.disabled = true;

            const loadingTask = pdfjsLib.getDocument(state.pdfUrl);
            state.pdfDoc = await loadingTask.promise;
            state.totalPages = state.pdfDoc.numPages;
            state.currentPage = 1;

            prevButton.disabled = state.totalPages <= 1;
            nextButton.disabled = state.totalPages <= 1;

            await fetchAnnotations();
            await renderPage(state.currentPage);
        } catch (error) {
            console.error('Error loading PDF:', error);
            pageInfo.textContent = 'Failed to load PDF';
            alert('Failed to load PDF');
        }
    }

    async function renderPage(pageNum) {
        if (!state.pdfDoc) return;

        try {
            const page = await state.pdfDoc.getPage(pageNum);
            const viewport = page.getViewport({ scale: state.scale });

            canvas.height = viewport.height;
            canvas.width = viewport.width;

            pageInfo.textContent = `Page ${pageNum} of ${state.totalPages}`;

            const renderContext = {
                canvasContext: ctx,
                viewport,
            };

            await page.render(renderContext).promise;

            const textContent = await page.getTextContent();
            textLayer.innerHTML = '';
            textLayer.style.height = `${viewport.height}px`;
            textLayer.style.width = `${viewport.width}px`;

            pdfjsLib.renderTextLayer({
                textContent,
                container: textLayer,
                viewport,
                textDivs: [],
                enhanceTextSelection: true,
            });

            annotationLayer.style.height = `${viewport.height}px`;
            annotationLayer.style.width = `${viewport.width}px`;

            state.currentPage = pageNum;
            drawAnnotations(pageNum);

            prevButton.disabled = pageNum <= 1;
            nextButton.disabled = pageNum >= state.totalPages;
        } catch (error) {
            console.error('Error rendering page:', error);
        }
    }

    async function fetchAnnotations() {
        if (!state.annotationApiBase) return;
        try {
            const response = await fetch(state.annotationApiBase, {
                headers: {
                    'Accept': 'application/json',
                },
                credentials: 'same-origin',
            });

            if (!response.ok) {
                throw new Error(`Failed to load annotations (${response.status})`);
            }

            const payload = await response.json();
            state.annotationsByPage.clear();

            if (Array.isArray(payload)) {
                payload.forEach((annotation) => {
                    const page = annotation.page || annotation.page_number || 1;
                    if (!state.annotationsByPage.has(page)) {
                        state.annotationsByPage.set(page, []);
                    }
                    state.annotationsByPage.get(page).push(normalizeAnnotation(annotation));
                });
            }
        } catch (error) {
            console.warn('Unable to fetch annotations:', error);
        }
    }

    function normalizeAnnotation(annotation) {
        return {
            id: annotation.id ?? null,
            page: annotation.page || annotation.page_number || state.currentPage,
            x: annotation.x ?? annotation.left ?? 0,
            y: annotation.y ?? annotation.top ?? 0,
            width: annotation.width ?? annotation.w ?? annotation.right ?? 0,
            height: annotation.height ?? annotation.h ?? annotation.bottom ?? 0,
            note: annotation.note ?? annotation.comment ?? '',
        };
    }

    function drawAnnotations(pageNum) {
        annotationLayer.innerHTML = '';
        const annotations = state.annotationsByPage.get(pageNum) || [];
        if (!annotations.length) return;

        annotations.forEach((annotation) => {
            const highlight = document.createElement('div');
            highlight.className = 'annotation-highlight';

            highlight.style.left = `${annotation.x * canvas.width}px`;
            highlight.style.top = `${annotation.y * canvas.height}px`;
            highlight.style.width = `${annotation.width * canvas.width}px`;
            highlight.style.height = `${annotation.height * canvas.height}px`;

            if (annotation.id != null) {
                highlight.dataset.annotationId = annotation.id;
            }

            highlight.title = annotation.note ? annotation.note : 'Click to open threaded chat';

            highlight.addEventListener('click', (event) => {
                event.stopPropagation();
                openThread(annotation.id);
            });

            annotationLayer.appendChild(highlight);
        });
    }

    function handleSelection() {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
            return;
        }

        const range = selection.getRangeAt(0);
        if (!textLayer.contains(range.commonAncestorContainer)) {
            selection.removeAllRanges();
            return;
        }

        const selectionRect = range.getBoundingClientRect();
        const canvasRect = canvas.getBoundingClientRect();

        if (!selectionRect || selectionRect.width === 0 || selectionRect.height === 0) {
            selection.removeAllRanges();
            return;
        }

        const x = (selectionRect.left - canvasRect.left) / canvasRect.width;
        const y = (selectionRect.top - canvasRect.top) / canvasRect.height;
        const width = selectionRect.width / canvasRect.width;
        const height = selectionRect.height / canvasRect.height;

        selection.removeAllRanges();

        const note = prompt('Add a note for this highlight (optional):', '');
        if (note === null) {
            return;
        }

        const annotation = {
            id: null,
            page: state.currentPage,
            x,
            y,
            width,
            height,
            note: note.trim(),
        };

        addAnnotation(annotation);
        saveAnnotation(annotation).catch((error) => console.error('Failed to save annotation:', error));
    }

    function addAnnotation(annotation) {
        if (!state.annotationsByPage.has(annotation.page)) {
            state.annotationsByPage.set(annotation.page, []);
        }
        state.annotationsByPage.get(annotation.page).push(annotation);
        if (annotation.page === state.currentPage) {
            drawAnnotations(annotation.page);
        }
    }

    async function saveAnnotation(annotation) {
        if (!state.annotationApiBase) return;

        const payload = {
            page: annotation.page,
            x: annotation.x,
            y: annotation.y,
            width: annotation.width,
            height: annotation.height,
            note: annotation.note,
        };

        const response = await fetch(state.annotationApiBase, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error(`Failed to save annotation (${response.status})`);
        }

        const saved = await response.json();
        if (saved && saved.id != null) {
            annotation.id = saved.id;
            annotation.note = saved.note ?? annotation.note;
        }
    }

    async function deleteAnnotation(annotationId) {
        if (!annotationId) return;
        const url = `/api/annotation/${annotationId}/delete/`;
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                },
                credentials: 'same-origin',
            });
            if (!response.ok) {
                throw new Error(`Failed to delete annotation (${response.status})`);
            }

            state.annotationsByPage.forEach((annotations, page) => {
                state.annotationsByPage.set(
                    page,
                    annotations.filter((item) => item.id !== annotationId),
                );
            });

            drawAnnotations(state.currentPage);
        } catch (error) {
            console.error(error);
        }
    }

    function openThread(annotationId) {
        const message = annotationId
            ? `Threaded chat coming soon for annotation #${annotationId}`
            : 'Threaded chat coming soon for this highlight.';
        alert(message);
    }

    function getCsrfToken() {
        const name = 'csrftoken=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookies = decodedCookie.split(';');
        for (let i = 0; i < cookies.length; i += 1) {
            let cookie = cookies[i];
            while (cookie.charAt(0) === ' ') {
                cookie = cookie.substring(1);
            }
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length, cookie.length);
            }
        }
        return '';
    }

    function bindPdfLinks() {
        const links = document.querySelectorAll('.pdf-link[data-pdf-url]');
        links.forEach((link) => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const url = link.getAttribute('data-pdf-url');
                const pdfId = link.getAttribute('data-pdf-id');
                loadPdfFromLink(url, pdfId ? Number(pdfId) : null);
            });
        });
    }

    function loadPdfFromLink(url, pdfId) {
        if (!url) return;

        state.pdfUrl = url;
        state.pdfId = pdfId || null;
        state.annotationApiBase = pdfId ? `/api/pdf/${pdfId}/annotations/` : null;

        state.annotationsByPage.clear();
        loadDocument();
    }

    window.loadPDF = loadPdfFromLink;

    window.renderPage = renderPage;
    window.drawAnnotations = drawAnnotations;
    window.saveAnnotation = saveAnnotation;
    window.openThread = openThread;
    window.deleteAnnotation = deleteAnnotation;
});

