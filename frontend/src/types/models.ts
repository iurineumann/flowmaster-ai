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

export interface ActiveModuleConfig extends SystemModuleDetail, UserModulePreference {}

export interface DashboardConfig {
    theme: string;
    activeModules: ActiveModuleConfig[];
}

// --- Tipos de Dados dos Agentes ---

export interface KnowledgeSuggestion {
    title: string;
    summary: string;
    score: number;
    source: string;
    link: string;
}

export interface ContextoAgregadoResponse {
    user_id: number;
    foco_critico: string;
    titulo_foco: string;
    resumo_ia: string;
    tags_tecnicas: string[];
    urgencia: number;
    sugestoes_conhecimento: KnowledgeSuggestion[];
}

// Skills
export interface SkillAgentResponse {
    user_id: number;
    contexto: string;
    // ✅ CORREÇÃO: 'sugestoes' alterado para 'suggestions' (para bater com o backend)
    suggestions: {
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