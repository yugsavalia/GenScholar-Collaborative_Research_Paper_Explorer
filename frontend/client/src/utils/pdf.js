import * as pdfjsLib from 'pdfjs-dist';

pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export const loadPdf = async (url) => {
  try {
    const loadingTask = pdfjsLib.getDocument(url);
    const pdf = await loadingTask.promise;
    return pdf;
  } catch (error) {
    console.error('Error loading PDF:', error);
    throw error;
  }
};

export const getTextContent = async (page) => {
  try {
    const textContent = await page.getTextContent();
    return textContent;
  } catch (error) {
    console.error('Error getting text content:', error);
    return null;
  }
};
