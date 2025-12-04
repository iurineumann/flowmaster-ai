// frontend/src/services/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { TokenResponse } from '../types/auth';

interface AuthContextType {
  token: string | null;
  userId: number | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function decodeJwt(token: string): { exp?: number } {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return {};
    const decoded = JSON.parse(atob(parts[1]));
    return { exp: decoded.exp };
  } catch {
    return {};
  }
}

function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  const { exp } = decodeJwt(token);
  if (!exp) return false; 
  return Date.now() >= (exp * 1000); // Compara em milissegundos
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    // Verifica se o token existente (access_token) é válido
    const storedToken = localStorage.getItem('access_token');
    if (isTokenExpired(storedToken)) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_id');
      return null;
    }
    return storedToken;
  });
  
  const [userId, setUserId] = useState<number | null>(() => {
    const id = localStorage.getItem('user_id');
    return id ? parseInt(id, 10) : null;
  });

  const isAuthenticated = !!token;

  const storeToken = (newToken: string, newUserId: number) => {
      localStorage.setItem('access_token', newToken);
      localStorage.setItem('user_id', newUserId.toString());
      setToken(newToken);
      setUserId(newUserId);
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const formBody = new URLSearchParams();
      formBody.append('username', username);
      formBody.append('password', password);

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formBody.toString(),
      });

      if (!response.ok) {
        throw new Error('Falha na autenticação');
      }

      const data: TokenResponse = await response.json();
      storeToken(data.access_token, data.user_id);
      return true;

    } catch (error) {
      console.error('Erro de Login:', error);
      logout();
      return false;
    }
  };

  const logout = () => {
    // ✅ CORREÇÃO: Limpa ambas as chaves
    localStorage.removeItem('access_token');
    localStorage.removeItem('jwt_token'); // Chave antiga
    localStorage.removeItem('user_id');
    setToken(null);
    setUserId(null);
  };

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (token && isTokenExpired(token)) {
        console.warn('⚠️ [Auth] Token expirado, fazendo logout...');
        logout();
      }
    }, 60000); 

    return () => clearInterval(intervalId);
  }, [token]);

  return (
    <AuthContext.Provider value={{ token, userId, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};