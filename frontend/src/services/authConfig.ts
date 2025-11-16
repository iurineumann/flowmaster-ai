// frontend/src/services/authConfig.ts

import { type Configuration, PublicClientApplication } from "@azure/msal-browser";

// Configurações do MSAL (lidas do .env do Vite)
const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_MSGRAPH_CLIENT_ID || "DEFAULT_CLIENT_ID",
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_MSGRAPH_TENANT_ID || "common"}`,
    redirectUri: import.meta.env.VITE_MSAL_REDIRECT_URI || "http://localhost:5173",
  },
  cache: {
    cacheLocation: "localStorage", // Armazena o token do Entra no localStorage
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return; // Evita logar PII
        console.log(`[MSAL Logger] [${level}] ${message}`);
      },
    },
  },
};

/**
 * Instância do MSAL que será usada em toda a aplicação.
 */
export const msalInstance = new PublicClientApplication(msalConfig);

/**
 * Escopos necessários para a aplicação.
 * 'openid', 'profile', 'email' são necessários para obter o ID Token.
 */
export const loginRequest = {
  scopes: ["openid", "profile", "email"]
};