// frontend/src/types.ts

/** Define o formato dos dados de configuração do sistema (backend/db) */
export interface SystemModuleDetail {
  id: string; // Ex: 'context_agent'
  name: string;
  description: string;
  api_endpoint: string; // Ex: '/contexto/agregado' (sem user_id)
  grid_column_span: number; // Define a largura na grade (ex: 2 para 2fr)
}

/** Define o formato dos dados de preferência do usuário (backend/db) */
export interface UserModulePreference {
  module_id: string; // Ex: 'context_agent'
  user_id: number;
  is_active: boolean;
  display_order: number;
}

/** Combinação da Configuração de Sistema e Preferência de Usuário para um módulo ativo */
export interface ActiveModuleConfig extends SystemModuleDetail, UserModulePreference {
  // api_endpoint_full agora contém o caminho completo e o ID do usuário para a chamada de dados
  api_endpoint_full: string; 
}

/** Define a estrutura completa de configuração do dashboard. */
export interface DashboardConfig {
  theme: string;
  activeModules: ActiveModuleConfig[];
}

// --- Tipagem dos Dados Retornados pelos Agentes ---

// Dados do Agente de Contexto (id: 'context_agent')
export interface ContextAgentData {
    user_id: number;
    foco_atual_titulo: string;
    resumo_ia: string;
    numero_itens_agregados: number;
    proxima_reuniao: string;
    sugestoes_conhecimento: any[]; 
}

// Dados do Agente de Skill (id: 'skill_agent')
export interface SkillSuggestion {
    title: string;
    score: number;
    link?: string;
}

export interface SkillAgentData {
    suggestions: SkillSuggestion[];
}

// Dados do Agente de Reserva (id: 'reserve_agent')
export interface ReserveAgentData {
    suggestion: string;
    action_required: boolean; // Novo: Indica se a sugestão é crítica/requer ação imediata
    link_to_map: string | null; // Novo: Link opcional para o mapa de reservas
}

// Tipo de união para os dados dinâmicos do painel (uso genérico)
export type AgentData = ContextAgentData | SkillAgentData | ReserveAgentData | any; 

// Tipagem para as Props do Componente
export interface AgentPanelProps {
  moduleConfig: ActiveModuleConfig;
}