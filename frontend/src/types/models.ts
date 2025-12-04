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
    usuario: string;
    funcao: string;
    projeto_atual: string;
    sprint_atual: string;
    tarefas_pendentes: number;
    proxima_reuniao: string | null;
    alertas: string[];
}

export interface SkillItem {
    skill: string;
    relevancia: string;
    motivo: string;
    summary?: string;
    type?: string;
    tags?: string[];
    source?: string;
    link?: string;
}

export interface SkillAgentResponse {
    suggestions: SkillItem[];
}

// Reserva (Alinhado com reserve.py)
export interface ReserveAgentResponse {
    is_suggested: boolean;
    resource_name: string | null;
    time_slot: string | null;
    reason: string | null;
}

// Reunião (Alinhado com meeting.py)
export interface MeetingAgentResponse {
    is_required: boolean;
    title: string;
    duration_minutes: number;
    suggested_agenda: string[];
    context_source: string;
}

// --- Tipos para Azure DevOps (ADO) ---
export interface AdoConnection {
    id: number;
    user_id: number;
    organization_url: string;
    is_active: boolean;
}

export interface AdoWorkItem {
    id: number;
    type: string; 
    title: string;
    state: string;
    url: string;
    project: string;
    organization: string;
}

// --- Admin Stats ---
export interface SystemStats {
    total_llm_calls: number;
    cache_hits: number;
    cache_misses: number;
    cache_efficiency: string;
    active_ws_connections: number;
    registered_users: number;
}

export interface CriticalBugAlert {
    type: "CRITICAL_BUG_ALERT";
    title: string;
    urgency: number;
    detail: string;
}