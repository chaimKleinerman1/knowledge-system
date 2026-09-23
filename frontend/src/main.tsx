import './index.css';

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from '@/app/App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('The page is missing the "root" element.');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
