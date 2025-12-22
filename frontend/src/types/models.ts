// frontend/src/types/models.ts

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

export interface CriticalBugAlert {
    type: "CRITICAL_BUG_ALERT";
    title: string;
    urgency: number;
    detail: string;
}














export interface UserConfig {
    user_id: number;
    theme: string;
    modules: UserModulePreference[];
}

export interface UserModulePreference {
    module_id: string;
    is_active: boolean;
    display_order: number;
}

export interface SystemModuleDetail {
    id: string;
    name: string;
    description: string;
    api_endpoint: string;
    grid_column_span: number;
}

export interface ActiveModuleConfig extends SystemModuleDetail, UserModulePreference {}

export interface ContextoAgregadoResponse {
    usuario: string;
    funcao: string;
    projeto_atual: string;
    sprint_atual: string;
    tarefas_pendentes: number;
    proxima_reuniao: string | null;
    alertas: string[];
}

// ✅ ATUALIZADO: Dados para o Modal de Skills
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

export interface ReserveAgentResponse {
    is_suggested: boolean;
    resource_name: string | null;
    time_slot: string | null;
    reason: string | null;
    location?: string;
}

export interface MeetingAgentResponse {
    is_required: boolean;
    title: string;
    duration_minutes: number;
    suggested_agenda: string[];
    context_source: string;
    priority?: "Alta" | "Média" | "Baixa";
}

export interface AdoConnection {
    id: number;
    organization_url: string;
    is_active: boolean;
    has_pat: boolean;
}

export interface AdoWorkItem {
    id: number;
    title: string;
    state: string;
    type: string;
    url: string;
    project: string;
    organization: string;
}

export interface SystemStats {
    total_llm_calls: number;
    cache_hits: number;
    cache_misses: number;
    cache_efficiency: string;
    active_ws_connections: number;
    registered_users: number;
}