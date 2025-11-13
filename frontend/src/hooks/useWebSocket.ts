import { useState, useEffect, useCallback } from 'react';
import type { AppNotification } from '../types/notifications';
import { useAuth } from '../services/AuthContext';

// URL do WebSocket: Deve ser lida de uma variável de ambiente (ws://localhost:8000)
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const useWebSocket = () => {
  const { token, isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (!isAuthenticated || !token) {
      return;
    }

    // 🚨 Conecta ao WS, passando o JWT como query parameter (Token de Autenticação)
    const wsUrl = `${WS_BASE_URL}/api/v1/notifications/ws?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ WebSocket conectado.');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: AppNotification = JSON.parse(event.data);
        console.log('🔔 Nova Notificação:', data);
        setNotifications((prev) => [data, ...prev].slice(0, 10)); // Mantém as 10 mais recentes
        // Aqui, você chamaria uma função para exibir um Toast/Pop-up
      } catch (e) {
        console.error('Erro ao parsear notificação:', e, event.data);
      }
    };

    ws.onclose = (event) => {
      console.log(`🛑 WebSocket desconectado. Código: ${event.code}`);
      setIsConnected(false);
      // Tenta reconectar após um delay, exceto se a desconexão for 401 (Autenticação)
      if (event.code !== 4001) { // Código 4001 simula o 401 HTTP (não é um código padrão WS)
         setTimeout(connect, 5000);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Erro no WebSocket:', error);
      ws.close();
    };

    return () => {
      ws.close(); // Função de limpeza
    };
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (isAuthenticated) {
      return connect();
    }
  }, [isAuthenticated, connect]);

  return { notifications, isConnected };
};