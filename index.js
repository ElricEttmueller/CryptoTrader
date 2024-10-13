import React from 'react';
import { createRoot } from 'react-dom/client';  // Import createRoot from React 18
import App from './App';

const container = document.getElementById('root');  // Get the root element
const root = createRoot(container);  // Create a React 18 root

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
