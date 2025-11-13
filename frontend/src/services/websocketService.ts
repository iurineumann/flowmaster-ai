// Squad 2: Serviço WebSocket para Alertas Críticos
import type { CriticalBugAlert } from '../types/models';

// Variável de ambiente
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL;
const WS_ENDPOINT = '/notifications/ws';

// Tipo de função para o callback de alerta
export type AlertHandler = (alert: CriticalBugAlert) => void;

let websocket: WebSocket | null = null;
let alertHandler: AlertHandler | null = null;

const connectWebSocket = (token: string) => {
    // Fecha a conexão antiga, se existir
    if (websocket) {
        websocket.close();
    }

    // A conexão WS usa o token JWT como parâmetro de query para autenticação no FastAPI
    const wsUrl = `${WS_BASE_URL}${WS_ENDPOINT}?token=${token}`;
    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('✅ [WebSocket] Conexão estabelecida.');
    };

    websocket.onmessage = (event) => {
        try {
            const data: CriticalBugAlert = JSON.parse(event.data);
            console.log('🔔 [WebSocket] Mensagem recebida:', data);
            
            // Verifica se é um alerta crítico e se há um handler
            if (data.type === 'CRITICAL_BUG_ALERT' && alertHandler) {
                alertHandler(data);
            }
        } catch (e) {
            console.error('❌ [WebSocket] Erro ao processar mensagem:', e);
        }
    };

    websocket.onclose = (event) => {
        console.warn('❌ [WebSocket] Conexão fechada. Tentando reconexão em 5s...', event.reason);
        // Implementação de reconexão robusta (melhor prática)
        setTimeout(() => {
            const newToken = localStorage.getItem('jwt_token');
            if (newToken) {
                connectWebSocket(newToken);
            } else {
                console.error("Token JWT não encontrado. Não é possível reconectar.");
            }
        }, 5000);
    };

    websocket.onerror = (error) => {
        console.error('🔥 [WebSocket] Erro fatal:', error);
        // O onclose será chamado logo após o onerror.
    };
};

// Funções públicas para a interface do serviço
export const initWebSocket = (token: string, handler: AlertHandler) => {
    alertHandler = handler;
    connectWebSocket(token);
};

export const closeWebSocket = () => {
    if (websocket) {
        websocket.close();
        websocket = null;
    }
};