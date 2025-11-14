// frontend/src/services/AuthContext.tsx

import React, { createContext, useContext, useState, type ReactNode } from 'react';
// ✅ CORREÇÃO: import type
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

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [userId, setUserId] = useState<number | null>(() => {
    const id = localStorage.getItem('user_id');
    return id ? parseInt(id, 10) : null;
  });

  const isAuthenticated = !!token;

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

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_id', data.user_id.toString());
      setToken(data.access_token);
      setUserId(data.user_id);
      return true;

    } catch (error) {
      console.error('Erro de Login:', error);
      logout();
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    setToken(null);
    setUserId(null);
  };

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