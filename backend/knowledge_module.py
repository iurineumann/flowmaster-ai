# backend/knowledge_module.py (CONTEÚDO COMPLETO COM CORREÇÃO E NOVA FUNÇÃO DE SKILLS)

from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio 
import os
# Importa APENAS o serviço REAL para LLM
from .services.llm_service import analyze_context_with_llm_real
from .services.vector_db_service import find_relevant_document_real
from .llm_optimization import ContextSummaryResponse, SkillSuggestionsResponse, SkillSuggestionItem, get_context_summary_prompt

# --- Modelos de K-Search (Pydantic) ---\
class KnowledgeSuggestion(BaseModel):
    title: str
    summary: str
    score: float 
    source: str
    link: str

# --- Dados MOCKADOS (Obrigatórios para o Mock de Crise) ---\
MOCK_KNOWLEDGE_SUGGESTIONS: List[KnowledgeSuggestion] = [
    KnowledgeSuggestion(
        title="Protocolo V3 de Criptografia - Guia de Migração",
        summary="Documentação oficial para a migração para o novo protocolo de segurança V3, focado em compliance PCI DSS. Requer atualização da biblioteca 'crypto-flow'.",
        score=95.0,
        source="Confluence",
        link="https://docs.flowmaster.ai/confluence/crypto-v3-guide"
    ),
    KnowledgeSuggestion(
        title="Checklist de Debugging de Falhas de Gateway",
        summary="Lista de verificação passo a passo para diagnosticar erros 500 em transações de pagamento via Gateway_Alpha.",
        score=88.5,
        source="GitLab Wiki",
        link="https://gitlab.flowmaster.ai/wiki/gateway-alpha-checklist"
    ),
]

# --- Mock de Skills (para a nova função) ---
MOCK_SKILL_SUGGESTIONS_RESPONSE = SkillSuggestionsResponse(
    suggestions=[
        SkillSuggestionItem(
            title="Criptografia Assimétrica e Padrões PCI DSS",
            relevance_score=98
        ),
        SkillSuggestionItem(
            title="Debugging e Profiling de Aplicações Python Assíncronas",
            relevance_score=85
        )
    ]
)

# --- Função Principal para o Context Agent (LLM) ---
# A função de entrada que a API chama é o serviço REAL assíncrono.
analyze_context_with_llm = analyze_context_with_llm_real

# --- 🎯 NOVA FUNÇÃO PRINCIPAL PARA O SKILL AGENT (LLM MOCKADO) ---
async def analyze_skills_with_llm(raw_context: str) -> SkillSuggestionsResponse:
    """
    Função facade para a análise de skills. Atualmente usa um MOCK assíncrono.
    Em produção, chamaria um LLM real para obter sugestões de Skill.
    """
    print("🧠 [SKILL-AGENT] Usando MOCK de sugestão de skills.")
    # Simula latência de chamada LLM
    await asyncio.sleep(0.5) 
    return MOCK_SKILL_SUGGESTIONS_RESPONSE


# --- Função Principal para o K-Search (CORRIGIDO) ---
async def find_relevant_document(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Função facade para a busca de conhecimento (Vector DB). 
    Tenta o serviço real, usa o MOCK assíncrono como fallback em caso de falha.
    """
    try:
        # Tenta a busca REAL (que é async em vector_db_service.py)
        print("🧠 [K-SEARCH] Iniciando busca vetorial para: '%s...'" % query_text[:50])
        return await find_relevant_document_real(query_text, top_k)
    except Exception as e:
        print(f"❌ [K-SEARCH] Falha na integração com Vector DB: {e}. Usando MOCK de sugestões como fallback.")
        
        await asyncio.sleep(0) # Garante que a função é awaitable
        
        # Retorna o mock estruturado
        # Utilizamos model_dump() (Pydantic v2)
        results = [s.model_dump() for s in MOCK_KNOWLEDGE_SUGGESTIONS]
        
        return results[:top_k]