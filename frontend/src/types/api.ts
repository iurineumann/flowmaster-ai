export interface ContextAgentData {
  user_id: number;
  foco_critico: string;
  foco_detalhe: string;
  resumo_llm: {
    focus_title: string;
    summary_analysis: string;
    urgency_score: number;
    technical_tags: string[];
  };
  sugestoes_conhecimento: {
    title: string;
    summary: string;
    score: number;
    link: string;
  }[];
}

export interface SkillAgentData {
  suggestions: {
    title: string;
    relevance_score: number;
    link?: string;
  }[];
}

export interface ReserveAgentData {
  is_suggested: boolean;
  resource_name: string;
  time_slot: string;
  reason: string;
  link_to_map?: string;
}
