// frontend/src/main.tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './services/AuthContext';
// ❌ REMOVIDO: import { PublicClientApplication } from '@azure/msal-browser';
// ❌ REMOVIDO: import { MsalProvider } from '@azure/msal-react';
// ❌ REMOVIDO: import { msalConfig } from './services/authConfig'; 

// ❌ REMOVIDO: const msalInstance = new PublicClientApplication(msalConfig);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* ❌ REMOVIDO: <MsalProvider instance={msalInstance}> */}
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    {/* ❌ REMOVIDO: </MsalProvider> */}
  </React.StrictMode>,
);