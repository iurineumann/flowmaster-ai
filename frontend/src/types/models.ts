// frontend/src/types/models.ts

// --- Tipos de Configuração ---
export interface UserModulePreference {
    module_id: string;
    is_active: boolean;
    display_order: number;
}

export interface UserConfig {
    user_id: number;
    theme: string;
    modules: UserModulePreference[];
}

export interface SystemModuleDetail {
    id: string;
    name: string;
    description: string;
    api_endpoint: string;
    grid_column_span: number;
}

// Tipo combinado para o Dashboard
export interface ActiveModuleConfig extends SystemModuleDetail, UserModulePreference {}

// --- Tipos de Dados dos Agentes ---

// Contexto (Corrigido para bater com backend/api/context.py)
export interface ContextoAgregadoResponse {
    user_id: number;
    foco_critico: string;      // Ex: "CLIENTE_X"
    titulo_foco: string;       // Ex: "BUG CRÍTICO..."
    resumo_ia: string;         // Texto do resumo
    tags_tecnicas: string[];
    urgencia: number;
    sugestoes_conhecimento: {
        title: string;
        summary: string;
        score: number;
        link: string;
        source: string;
    }[];
}

// Skills
export interface SkillAgentResponse {
    user_id: number;
    contexto: string;
    sugestoes: {
        title: string;
        relevance_score: number;
        link?: string;
    }[];
}

// Reserva
export interface ReserveAgentResponse {
    is_suggested: boolean;
    resource_name: string;
    time_slot: string | null;
    reason: string;
}

// Reunião
export interface MeetingAgentResponse {
    is_required: boolean;
    title: string;
    duration_minutes: number;
    suggested_agenda: string[];
    context_source: string;
}

// --- Tipos de Notificação ---
export interface CriticalBugAlert {
    type: "CRITICAL_BUG_ALERT";
    title: string;
    urgency: number;
    detail: string;
}