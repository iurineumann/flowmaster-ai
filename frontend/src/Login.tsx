// frontend/src/Login.tsx

import React, { useState } from 'react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./services/authConfig";
import type { AuthError } from "@azure/msal-browser";

// O onLoginSuccess (do nosso AuthContext) ainda é necessário 
// para sinalizar ao App.tsx que trocamos o token.
interface LoginProps {
    onLoginSuccess: () => void;
}

// Interface para o request de troca de token
interface EntraTokenRequest {
  entra_id_token: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
    const { instance } = useMsal();
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleMicrosoftLogin = async () => {
        setLoading(true);
        setError(null);
        try {
            // 1. Abre o Popup de Login da Microsoft
            const msalResponse = await instance.loginPopup(loginRequest);
            
            if (msalResponse.idToken) {
                // 2. Token do Entra ID obtido com sucesso.
                // Agora, trocamos pelo nosso JWT interno chamando o backend
                const payload: EntraTokenRequest = {
                    entra_id_token: msalResponse.idToken
                };

                const tokenExchangeResponse = await fetch(`${API_BASE_URL}/api/v1/auth/entra_login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!tokenExchangeResponse.ok) {
                    throw new Error("Falha ao trocar o token do Entra ID pelo token interno.");
                }

                const internalTokenData = await tokenExchangeResponse.json();

                // 3. Armazena o token INTERNO (o único que o resto da app usa)
                localStorage.setItem('jwt_token', internalTokenData.access_token);
                localStorage.setItem('user_id', internalTokenData.user_id.toString());
                
                // 4. Sinaliza ao App.tsx que o login interno foi concluído
                onLoginSuccess();

            } else {
                throw new Error("Login da Microsoft falhou: ID Token não retornado.");
            }

        } catch (e) {
            const authError = e as AuthError;
            console.error('Erro de Autenticação MSAL:', authError);
            if (authError.errorCode === "user_cancelled") {
                setError("Login cancelado pelo usuário.");
            } else {
                setError(authError.errorMessage || "Ocorreu um erro desconhecido no login.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '40px', maxWidth: '400px', margin: '100px auto', border: '1px solid #ccc', borderRadius: '8px', textAlign: 'center' }}>
            <h2 className="text-2xl font-bold">FlowMaster AI</h2>
            <p className="text-muted-foreground mb-6">Login (T2M / Microsoft Entra ID)</p>
            
            <button 
                onClick={handleMicrosoftLogin}
                style={{ 
                    width: '100%', 
                    padding: '10px', 
                    backgroundColor: '#0078D4', // Cor da Microsoft
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '16px'
                }}
                disabled={loading}
            >
                {loading ? 'Aguardando Microsoft...' : 'Entrar com Microsoft'}
            </button>

            {error && <p style={{ color: 'red', marginTop: '15px' }}>{error}</p>}
        </div>
    );
};

export default Login;