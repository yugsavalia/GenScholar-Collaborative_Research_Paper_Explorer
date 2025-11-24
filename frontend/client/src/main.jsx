import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import './styles/custom.css';
import './utils/pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import { initializeCsrfToken } from './utils/csrf';
import { initTheme } from './utils/theme';

// Initialize theme on app load
initTheme();

// Initialize CSRF token on app load
initializeCsrfToken().catch(err => {
  console.warn('Failed to initialize CSRF token on app load:', err);
});

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Failed to find the root element');

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
