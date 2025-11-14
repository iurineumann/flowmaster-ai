// frontend/src/services/apiClient.ts

import axios from 'axios';
// ✅ CORREÇÃO: Uso de 'import type' para todas as interfaces
import type { 
    UserConfig, 
    SystemModuleDetail, 
    ContextoAgregadoResponse,
    SkillAgentResponse,
    ReserveAgentResponse,
    MeetingAgentResponse
} from '../types/models';

// Lê a URL base do ambiente ou usa o proxy padrão
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para adicionar o Token JWT automaticamente
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

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
    updateUserModules: async (preferences: any[]) => {
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
        return response.data; // Retorna { response: str, context_used: [] }
    }
};