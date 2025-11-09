// frontend/src/interfaces.ts
// Define os Tipos de Dados (Interfaces) para o Backend

// 1. Contexto Agregado (API /contexto/agregado)
export interface ContextoAgregado {
    user_id: number;
    foco_atual_titulo: string;
    resumo_ia: string;
    numero_itens_agregados: number;
    proxima_reuniao: string;
    sugestoes_conhecimento: SugestaoConhecimento[];
}

// Sub-interface para K-Search
export interface SugestaoConhecimento {
    score: string;
    title: string;
    content_preview: string;
    doc_id: string;
}

// 2. Skill-Boost (API /skill/suggestions)
export interface SkillSuggestion {
    type: string; // 'course' | 'expert' | 'info'
    title: string;
    context_reason: string;
}

// 3. Reserva Inteligente (API /reserva/suggestion)
export interface ReserveSuggestion {
    resource_id: string;
    resource_type: string; // 'desk' | 'meeting_room' | 'quiet_pod'
    suggested_location: string;
    reason: string;
}