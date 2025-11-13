// Squad 1: Modelos de Dados (TypeScript)

// Módulos (usado na rota /config/user)
export interface UserModulePreference {
    module_id: string;
    is_active: boolean;
    display_order: number;
}

// Configuração principal do dashboard (/config/user)
export interface UserConfig {
    user_id: number;
    theme: string;
    modules: UserModulePreference[];
}

// Sugestões de Conhecimento (k-search)
export interface KnowledgeSuggestion {
    title: string;
    summary: string;
    score: number;
    source: string;
    link: string;
}

// Resposta agregada do contexto (/contexto/agregado)
export interface ContextoAgregadoResponse {
    user_id: number;
    foco_critico: {
        title: string;
        summary_analysis: string;
        urgency_score: number;
    };
    sugestoes_conhecimento: KnowledgeSuggestion[];
    // Outros dados que virão de outros agentes (skill, reserve, etc.)
}

// Alerta Crítico (Formato da mensagem WS - Usado pelo Squad 2)
export interface CriticalBugAlert {
    type: "CRITICAL_BUG_ALERT";
    title: string;
    urgency: number;
    detail: string;
}