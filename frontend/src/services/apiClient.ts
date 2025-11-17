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
    SystemStats // NOVO
} from '../types/models';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use((config) => {
    // Busca 'access_token' (armazenado pelo AuthContext/Login)
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('✅ [API] Token adicionado ao header Authorization');
    } else {
        console.warn('⚠️ [API] Nenhum token encontrado em localStorage');
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            console.warn('⚠️ [API] Erro 401 - Token inválido ou expirado. Fazendo logout.');
            localStorage.removeItem('jwt_token');
            localStorage.removeItem('user_id');
            // Redireciona para login
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// --- Métodos da API ---

export const apiService = {
    // Configuração
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

    // Agentes (Dados Reais)
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
    
    // Chat
    sendChatQuery: async (message: string) => {
        const response = await apiClient.post('/chat/query', { message });
        return response.data;
    },
    
    // ADO
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

    // --- NOVO (Admin) ---
    getAdminStats: async () => {
        const response = await apiClient.get<SystemStats>('/admin/stats');
        return response.data;
    }
};