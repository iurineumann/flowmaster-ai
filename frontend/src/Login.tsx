// frontend/src/Login.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from './services/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios'; 

const Login: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [searchParams] = useSearchParams();

    const [error, setError] = useState<string | null>(null);
    const [loadingMsal, setLoadingMsal] = useState(false);
    const [loadingLocal, setLoadingLocal] = useState(false);
    
    const [localUsername, setLocalUsername] = useState('devuser');
    const [localPassword, setLocalPassword] = useState('devpass');

    // 1. Detectar retorno da Microsoft
    useEffect(() => {
        const code = searchParams.get('code');
        const state = searchParams.get('state'); 
        
        if (code && state) {
            handleEntraCallback(code, state); 
        }
    }, [searchParams]);

    // 2. Callback Manual
    const handleEntraCallback = async (code: string, state: string) => { 
        setLoadingMsal(true);
        window.history.replaceState({}, document.title, "/login");

        try {
            // Usamos caminho relativo para garantir o envio do cookie de sessão
            const response = await axios.post(
                `/api/v1/auth/entra/callback?state=${state}`, 
                { 
                    code, 
                    redirect_uri: window.location.origin + '/login' 
                },
                { withCredentials: true } 
            );

            const { access_token, user_id } = response.data;
            
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('user_id', user_id.toString());
            
            window.location.href = '/';

        } catch (err: any) {
            console.error("Erro no callback:", err);
            setError(err.response?.data?.detail || "Falha ao trocar código por token.");
            setLoadingMsal(false);
        }
    };

    // 3. Iniciar Login
    const handleMicrosoftLogin = () => {
        setLoadingMsal(true);
        const redirectUri = window.location.origin + '/login';
        // Inicia o fluxo no backend para gerar o cookie de sessão
        window.location.href = `/api/v1/auth/entra/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`;
    };

    // 4. Login Local
    const handleLocalLogin = async () => {
        setLoadingLocal(true);
        setError(null);
        const success = await login(localUsername, localPassword);
        if (!success) {
            setError("Falha no login local.");
            setLoadingLocal(false);
        } else {
            navigate('/');
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex items-center justify-center p-4">
            <Card className="w-full max-w-md shadow-xl">
                <CardHeader className="text-center space-y-1">
                    <CardTitle className="text-2xl font-bold">FlowMaster AI</CardTitle>
                    <p className="text-sm text-muted-foreground">
                        Entre para gerenciar seu contexto
                    </p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Button 
                        onClick={handleMicrosoftLogin}
                        className="w-full bg-[#0078D4] text-white hover:bg-[#005a9e] h-11"
                        disabled={loadingMsal || loadingLocal}
                    >
                        {loadingMsal ? (
                            <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processando...</>
                        ) : (
                            <div className="flex items-center justify-center gap-2">
                                <svg className="w-5 h-5" viewBox="0 0 23 23" xmlns="http://www.w3.org/2000/svg"><path fill="#f3f3f3" d="M0 0h23v23H0z"/><path fill="#f35325" d="M1 1h10v10H1z"/><path fill="#81bc06" d="M12 1h10v10H12z"/><path fill="#05a6f0" d="M1 12h10v10H1z"/><path fill="#ffba08" d="M12 12h10v10H12z"/></svg>
                                Entrar com Microsoft
                            </div>
                        )}
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-gray-300 dark:border-gray-700" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-background px-2 text-muted-foreground">Ou (Dev)</span>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Input 
                            placeholder="Usuário" 
                            value={localUsername} 
                            onChange={e => setLocalUsername(e.target.value)}
                        />
                        <Input 
                            type="password" 
                            placeholder="Senha" 
                            value={localPassword} 
                            onChange={e => setLocalPassword(e.target.value)}
                        />
                        <Button 
                            onClick={handleLocalLogin}
                            variant="outline"
                            className="w-full"
                            disabled={loadingMsal || loadingLocal}
                        >
                            {loadingLocal ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Entrar Localmente'}
                        </Button>
                    </div>

                    {error && (
                        <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" />
                            {error}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default Login;