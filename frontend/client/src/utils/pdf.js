import * as pdfjsLib from 'pdfjs-dist';
import { pdfjs as reactPdfjs } from 'react-pdf';

// Resolve worker URL from the installed pdfjs-dist package to ensure version match
const workerUrl = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString();
pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;
reactPdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

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
