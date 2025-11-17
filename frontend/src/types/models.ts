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

// --- 4. Tipos para Azure DevOps (ADO) ---

// Configuração da Conexão (GET /config/ado/connections)
export interface AdoConnection {
    id: number;
    user_id: number;
    organization_url: string;
    is_active: boolean;
}

// Configuração do Projeto (GET /config/ado/projects/{id})
export interface AdoProject {
    id: number;
    connection_id: number;
    project_name: string;
    is_active: boolean;
}

// Resposta do Agente (GET /ado/work_items)
export interface AdoWorkItem {
    id: number;
    type: string; // Bug, Task, etc.
    title: string;
    state: string;
    url: string;
    project: string;
    organization: string;
}

// --- NOVO (Admin Stats) ---
export interface SystemStats {
    total_llm_calls: number;
    cache_hits: number;
    cache_misses: number;
    cache_efficiency: string; // "0.0%"
    active_ws_connections: number;
    registered_users: number;
}