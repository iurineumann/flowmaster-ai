// frontend/src/services/apiClient.ts

import axios from 'axios';
import type { 
    UserConfig, 
    SystemModuleDetail, 
    ContextoAgregadoResponse,
    SkillAgentResponse,
    ReserveAgentResponse,
    MeetingAgentResponse,
    AdoConnection,
    AdoWorkItem,
    UserModulePreference,
    SystemStats
} from '../types/models';

// ✅ CORREÇÃO: Alterado de "/api" para "/api/v1" para bater com o Nginx e Backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

function getStoredToken(): string | null {
    return localStorage.getItem('access_token') || localStorage.getItem('jwt_token');
}

// ... (Restante do código de refresh token permanece igual) ...
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (err?: any) => void;
    originalRequest: any;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            if (token && prom.originalRequest && prom.originalRequest.headers) {
                prom.originalRequest.headers['Authorization'] = `Bearer ${token}`;
            }
            prom.resolve(apiClient(prom.originalRequest));
        }
    });
    failedQueue = [];
};

async function tryRefreshToken(): Promise<string | null> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return null;

    try {
        const plain = axios.create({ baseURL: API_BASE_URL, timeout: 15000 });
        const resp = await plain.post('/auth/refresh', { refresh_token: refreshToken });
        const newAccess = resp.data?.access_token;
        const newRefresh = resp.data?.refresh_token;

        if (newAccess) {
            localStorage.setItem('access_token', newAccess);
            if (newRefresh) localStorage.setItem('refresh_token', newRefresh);
            return newAccess;
        }
    } catch (err) {
        console.warn('Falha ao renovar token:', err);
        return null;
    }
    return null;
}

apiClient.interceptors.request.use((config: any) => {
    const token = getStoredToken();
    if (token) {
        if (!config.headers) config.headers = {};
        if (!config.headers['Authorization']) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        const status = error.response?.status;

        if (status === 401 && !originalRequest?._retry) {
            originalRequest._retry = true;
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject, originalRequest });
                });
            }
            isRefreshing = true;
            try {
                const newToken = await tryRefreshToken();
                if (newToken) {
                    processQueue(null, newToken);
                    if (originalRequest.headers) {
                        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                    } else {
                        originalRequest.headers = { Authorization: `Bearer ${newToken}` };
                    }
                    return apiClient(originalRequest);
                } else {
                    throw new Error('Refresh token inválido');
                }
            } catch (refreshErr) {
                processQueue(refreshErr, null);
                localStorage.removeItem('access_token');
                localStorage.removeItem('jwt_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user_id');
                window.location.href = '/login';
                return Promise.reject(refreshErr);
            } finally {
                isRefreshing = false;
            }
        }

        if (status === 401) {
            console.warn('⚠️ [API] Erro 401 - Token inválido ou expirado.');
            localStorage.removeItem('access_token');
            localStorage.removeItem('jwt_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_id');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const apiService = {
    getSystemModules: async () => {
        const response = await apiClient.get<SystemModuleDetail[]>('/config/modules');
        return response.data;
    },
    getUserConfig: async () => {
        const response = await apiClient.get<UserConfig>('/config/user');
        return response.data;
    },
    updateUserModules: async (preferences: UserModulePreference[]) => {
        const response = await apiClient.patch<UserConfig>('/config/user/modules', { preferences });
        return response.data;
    },
    getContexto: async () => {
        const response = await apiClient.get<ContextoAgregadoResponse>('/contexto/agregado');
        return response.data;
    },
    getSkills: async () => {
        const response = await apiClient.get<SkillAgentResponse>('/skill/sugestoes');
        return response.data;
    },
    getReserva: async () => {
        const response = await apiClient.get<ReserveAgentResponse>('/reserva/sugestao');
        return response.data;
    },
    getMeeting: async () => {
        const response = await apiClient.get<MeetingAgentResponse>('/meeting/sugestao');
        return response.data;
    },
    sendChatQuery: async (message: string) => {
        const response = await apiClient.post('/chat/query', { message });
        return response.data;
    },
    getAdoWorkItems: async () => {
        const response = await apiClient.get<AdoWorkItem[]>('/ado/work_items');
        return response.data;
    },
    getAdoConnections: async () => {
        const response = await apiClient.get<AdoConnection[]>('/config/ado/connections');
        return response.data;
    },
    createAdoConnection: async (organization_url: string) => {
        const response = await apiClient.post<AdoConnection>('/config/ado/connections', { organization_url });
        return response.data;
    },
    getAdminStats: async () => {
        const response = await apiClient.get<SystemStats>('/admin/stats');
        return response.data;
    },
    // ✅ Método Genérico para Atualizar Configuração (usado no Settings)
    updateUserConfig: async (config: any) => {
        // Se não houver rota específica, usamos a de módulos como base ou criamos uma nova
        // Por enquanto, vamos assumir que o backend aceita patch em /config/user
        const response = await apiClient.patch('/config/user', config);
        return response.data;
    }
};

export default apiClient;