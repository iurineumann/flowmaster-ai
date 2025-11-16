// frontend/src/main.tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './services/AuthContext.tsx';

// --- MSAL Imports ---
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./services/authConfig.ts";

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* O MsalProvider DEVE estar no topo */}
    <MsalProvider instance={msalInstance}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </MsalProvider>
  </React.StrictMode>,
);