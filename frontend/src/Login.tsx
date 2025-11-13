// frontend/src/Login.tsx (NOVO COMPONENTE)

import React, { useState } from 'react';

// Define a interface para o retorno do login
interface TokenData {
    access_token: string;
    user_id: number;
    token_type: string;
}

interface LoginProps {
    onLoginSuccess: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState('devuser'); // Padrão para mock
    const [password, setPassword] = useState('devpass'); // Padrão para mock
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        // O FastAPI/OAuth2 espera o formato `application/x-www-form-urlencoded`
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch(`${API_BASE_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Falha na autenticação.');
            }

            const data: TokenData = await response.json();
            
            // 1. Armazenar o Token no LocalStorage (ou SessionStorage)
            localStorage.setItem('jwt_token', data.access_token);
            
            // 2. Notificar o componente pai (App.tsx)
            onLoginSuccess(data.access_token);

        } catch (err: any) {
            setError(err.message || 'Erro de conexão com a API de Login.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '40px', maxWidth: '400px', margin: '100px auto', border: '1px solid #ccc', borderRadius: '8px' }}>
            <h2>FlowMaster AI - Login</h2>
            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '15px' }}>
                    <label>Usuário:</label>
                    <input 
                        type="text" 
                        value={username} 
                        onChange={(e) => setUsername(e.target.value)} 
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                        disabled={loading}
                    />
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <label>Senha:</label>
                    <input 
                        type="password" 
                        value={password} 
                        onChange={(e) => setPassword(e.target.value)} 
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                        disabled={loading}
                    />
                </div>
                <button 
                    type="submit" 
                    style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
                    disabled={loading}
                >
                    {loading ? 'Entrando...' : 'Entrar'}
                </button>
            </form>
            {error && <p style={{ color: 'red', marginTop: '15px' }}>{error}</p>}
            <p style={{ marginTop: '20px', fontSize: '0.8em', color: '#666' }}>
                Credenciais de Teste: Usuário: <strong>devuser</strong>, Senha: <strong>devpass</strong>
            </p>
        </div>
    );
};

export default Login;