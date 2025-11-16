# backend/knowledge_module.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional # ✅ 'Optional' ADICIONADO AQUI
import asyncio
import os

# Importa as implementações REAIS dos serviços
from .services.llm_service import analyze_context_with_llm_real
from .services.vector_db_service import find_relevant_document_real

# Importa os Schemas Pydantic
from .llm_optimization import ContextSummaryResponse, SkillSuggestionsResponse, SkillSuggestionItem

# --- 1. Facade para o Serviço de LLM ---
analyze_context_with_llm = analyze_context_with_llm_real

# --- 2. Facade para o K-Search (com Fallback Assíncrono) ---

class KnowledgeSuggestion(BaseModel):
    title: str
    summary: str
    score: float 
    source: str
    link: str

MOCK_KNOWLEDGE_SUGGESTIONS: List[KnowledgeSuggestion] = [
    KnowledgeSuggestion(
        title="Protocolo V3 de Criptografia - Guia de Migração",
        summary="Documentação oficial para a migração para o novo protocolo de segurança V3...",
        score=95.0,
        source="Confluence",
        link="https://docs.flowmaster.ai/confluence/crypto-v3-guide"
    ),
    KnowledgeSuggestion(
        title="Checklist de Debugging de Falhas de Gateway",
        summary="Lista de verificação passo a passo para diagnosticar erros 500...",
        score=88.5,
        source="GitLab Wiki",
        link="https://gitlab.flowmaster.ai/wiki/gateway-alpha-checklist"
    ),
]

async def find_relevant_document(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Função facade para a busca de conhecimento (Vector DB). 
    Tenta o serviço real, usa o MOCK assíncrono como fallback em caso de falha.
    """
    try:
        # Tenta a busca REAL (que é async em vector_db_service.py)
        return await find_relevant_document_real(query_text, top_k)
    except Exception as e:
        print(f"❌ [K-SEARCH] Falha na integração com Vector DB: {e}. Usando MOCK de sugestões como fallback.")
        
        # Fallback para o MOCK de forma assíncrona (resolve o TypeError)
        await asyncio.sleep(0) # Garante que a função é awaitable
        
        results = [s.model_dump() for s in MOCK_KNOWLEDGE_SUGGESTIONS]
        return results[:top_k]

# --- 3. Facade para o Agente de Skills (Implementação Real ou Erro) ---
async def analyze_skills_with_llm(context_summary: str) -> Optional[SkillSuggestionsResponse]:
    """
    Implementação real (placeholder) para análise de skills.
    Retorna None se o serviço não estiver pronto.
    """
    print(f"🧠 [LLM-SKILL] (Não implementado) Iniciando análise de skill para: '{context_summary[:50]}...'")
    await asyncio.sleep(0.1) 
    # Retorna None para indicar que o serviço não está pronto ou falhou
    return None
    