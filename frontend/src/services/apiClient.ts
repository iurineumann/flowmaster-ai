// Squad 1: Cliente REST API com Interceptor JWT

import axios from 'axios';

// Variável de ambiente configurada no .env
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor de Requisição: Adiciona o JWT a todas as chamadas
apiClient.interceptors.request.use(
    (config) => {
        // ** SIMULAÇÃO DE JWT: O frontend precisa armazenar o token após o Login. **
        // Usamos um token mockado no localStorage para o teste inicial
        const token = localStorage.getItem('jwt_token');

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// --- Funções de Serviço ---
import type { UserConfig, ContextoAgregadoResponse } from '../types/models';

export const fetchUserConfig = async (): Promise<UserConfig> => {
    const response = await apiClient.get<UserConfig>('/config/user');
    return response.data;
};

export const fetchContextoAgregado = async (): Promise<ContextoAgregadoResponse> => {
    const response = await apiClient.get<ContextoAgregadoResponse>('/contexto/agregado');
    return response.data;
};