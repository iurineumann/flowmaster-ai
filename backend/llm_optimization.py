# backend/llm_optimization.py

from pydantic import BaseModel, Field
from typing import List

# --- Schemas de Resposta da LLM (Pydantic) ---

# Schema para o Agente de Contexto (resumo do foco atual)
class ContextSummaryResponse(BaseModel):
    """
    Estrutura de resposta esperada do LLM para o Resumo do Contexto.
    Força a LLM a retornar um resumo conciso e tags de foco.
    """
    focus_title: str = Field(description="Título conciso do foco principal (Ex: 'BUG CRÍTICO - Falha de Criptografia').")
    summary_analysis: str = Field(description="Resumo da IA em no máximo 50 palavras, detalhando a urgência e o problema técnico subjacente.")
    technical_tags: List[str] = Field(description="3 a 5 termos-chave técnicos que definem o problema (Ex: ['Criptografia V3', 'PCI DSS', 'Gateway Alpha']).")
    urgency_score: int = Field(description="Pontuação de 1 a 100, onde 100 é a máxima urgência.")


# Schema para o Agente de Skills (sugestões de aprendizado)
class SkillSuggestionItem(BaseModel):
    """Um item individual de sugestão de skill."""
    title: str = Field(description="Título da Skill (Ex: 'Criptografia em Python - Nível Avançado').")
    relevance_score: int = Field(description="Pontuação de 0 a 100 indicando a relevância da skill para o foco atual.")

class SkillSuggestionsResponse(BaseModel):
    """Estrutura de resposta esperada do LLM para o Agente de Skills."""
    suggestions: List[SkillSuggestionItem]


# --- CONSTANTE DE FALLBACK DE CRISE (Adicionado para robustez do llm_service) ---
# Esta resposta é usada quando o LLM REAL falha para garantir que a crise seja notificada.
MOCK_SUMMARY_RESPONSE = ContextSummaryResponse(
    focus_title="BUG CRÍTICO: Falha no Pagamento",
    summary_analysis="O sistema de pagamento está inoperante devido a uma falha na implementação do novo protocolo de criptografia V3. Risco de exposição de dados e impacto financeiro. Urgência máxima para correção.",
    technical_tags=["Criptografia V3", "PCI DSS", "Gateway Alpha"],
    urgency_score=95
)


# --- Prompts Otimizados (Instruções) ---

def get_context_summary_prompt(raw_context: str) -> str:
    """
    Gera o prompt otimizado para a LLM produzir o Resumo de Contexto.
    Otimização: Role-Prompting, CoT, Instruções Detalhadas, JSON Schema.
    """
    
    return f"""
    Você é um **Analista de Crises Sênior (S.C.A.)** e Especialista em Risco (LGPD/PCI DSS).
    Sua tarefa é analisar o contexto BRUTO a seguir e fornecer uma análise crítica, concisa e orientada à ação.

    **Pense passo a passo (Chain-of-Thought):**
    1. **Identifique a entidade/projeto crítica** (Ex: CLIENTE_X, Gateway Alpha).
    2. **Avalie o risco de conformidade** (LGPD, PCI DSS, etc.) com base no contexto.
    3. **Determine a ação imediata** necessária.
    4. **Atribua a pontuação de urgência** (1-100) baseada no impacto financeiro e regulatório.

    **INSTRUÇÕES DE SAÍDA:**
    1. **FOCO** (`focus_title`): Título conciso da Crise. Deve começar com 'CRÍTICO' se a urgência for >= 90.
    2. **RESUMO** (`summary_analysis`): Resumo da análise (máx. 50 palavras), **focado em Risco e Ação**.
    3. **TAGS** (`technical_tags`): 3 a 5 termos-chave técnicos relevantes para o problema (Ex: ['Gateway Alpha', 'Criptografia V3', 'Bug 500']).
    4. **URGÊNCIA** (`urgency_score`): Pontuação de 1 a 100, onde 100 é a máxima urgência.

    **CONTEXTO BRUTO (Mascarado):**
    ---
    {raw_context}
    ---

    Sua resposta DEVE ser um objeto JSON que estritamente se encaixe no Schema Pydantic ContextSummaryResponse.
    """