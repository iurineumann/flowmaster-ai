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
    """
    # Em produção, o JSON Schema seria injetado aqui via métodos da biblioteca LLM
    
    return f"""
    Você é um Analista de Contexto Sênior (S.C.A.) e sua tarefa é analisar o contexto bruto
    a seguir e fornecer uma análise concisa.

    1. FOCO: Identifique o problema ou tarefa central mais urgente.
    2. RESUMO: Crie um resumo de análise de impacto com no máximo 50 palavras.
    3. TAGS: Identifique os 3 a 5 termos técnicos-chave do problema.
    4. URGÊNCIA: Atribua uma pontuação de urgência de 1 a 100.

    CONTEXTO BRUTO:
    ---
    {raw_context}
    ---

    Sua resposta DEVE ser um objeto JSON que estritamente se encaixe no seguinte esquema (JSON Schema):
    {ContextSummaryResponse.model_json_schema()}
    """