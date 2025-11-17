// frontend/src/Login.tsx

import React, { useState } from 'react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./services/authConfig";
import type { AuthError } from "@azure/msal-browser";
import { useAuth } from './services/AuthContext'; // Importa o AuthContext local
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/Card';
import { Button } from './components/ui/Button';

interface LoginProps {
  // onLoginSuccess não é mais necessário, pois o App.tsx (pai) 
  // reagirá à mudança no 'isAuthenticated' do useAuth().
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Login: React.FC<LoginProps> = () => {
    const { instance } = useMsal();
    const auth = useAuth(); // Hook do nosso AuthContext
    
    const [error, setError] = useState<string | null>(null);
    const [loadingMsal, setLoadingMsal] = useState(false);
    const [loadingLocal, setLoadingLocal] = useState(false);
    
    // --- Login Local (devuser) ---
    const handleLocalLogin = async () => {
        setLoadingLocal(true);
        setError(null);
        const success = await auth.login("devuser", "devpass");
        if (!success) {
            setError("Falha no login local (devuser/devpass). Verifique o backend.");
        }
        // Se sucesso, o App.tsx vai detectar a mudança em isAuthenticated
        setLoadingLocal(false);
    };

    // --- Login Microsoft (Entra ID) ---
    const handleMicrosoftLogin = async () => {
        setLoadingMsal(true);
        setError(null);
        try {
            const msalResponse = await instance.loginPopup(loginRequest);
            
            if (msalResponse.idToken) {
                const payload = { entra_id_token: msalResponse.idToken };

                const tokenExchangeResponse = await fetch(`${API_BASE_URL}/api/v1/auth/entra_login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!tokenExchangeResponse.ok) {
                    const err = await tokenExchangeResponse.json();
                    throw new Error(err.detail || "Falha ao trocar o token do Entra ID pelo token interno.");
                }

                const internalTokenData = await tokenExchangeResponse.json();

                // Armazena o token INTERNO (usando chave padronizada 'access_token')
                localStorage.setItem('access_token', internalTokenData.access_token);
                localStorage.setItem('user_id', internalTokenData.user_id.toString());
                
                // Força o AuthContext a recarregar o estado e o App.tsx a re-renderizar
                window.location.reload(); 

            } else {
                throw new Error("Login da Microsoft falhou: ID Token não retornado.");
            }

        } catch (e: any) {
            const authError = e as AuthError;
            if (authError.errorCode === "user_cancelled") {
                setError("Login cancelado pelo usuário.");
            } else {
                setError(e.message || "Ocorreu um erro desconhecido no login.");
            }
        } finally {
            setLoadingMsal(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
            <Card className="w-full max-w-md mx-4">
                <CardHeader>
                    <CardTitle className="text-2xl font-bold text-center text-primary">
                        FlowMaster AI
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Button 
                        onClick={handleMicrosoftLogin}
                        className="w-full bg-[#0078D4] text-white hover:bg-[#005a9e]"
                        disabled={loadingMsal || loadingLocal}
                    >
                        {loadingMsal ? 'Aguardando Microsoft...' : 'Entrar com Microsoft'}
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-card px-2 text-muted-foreground">
                                Ou (Desenvolvimento)
                            </span>
                        </div>
                    </div>

                    <Button 
                        onClick={handleLocalLogin}
                        variant="secondary"
                        className="w-full"
                        disabled={loadingMsal || loadingLocal}
                    >
                        {loadingLocal ? 'Entrando...' : 'Entrar como devuser'}
                    </Button>

                    {error && <p className="text-destructive text-sm text-center">{error}</p>}
                </CardContent>
            </Card>
        </div>
    );
};

export default Login;