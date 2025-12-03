# backend/knowledge_module.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio

# ✅ Importação corrigida
from .services.llm_service import analyze_context_with_llm_real
from .services.vector_db_service import find_relevant_document_real
from .llm_optimization import SkillSuggestionsResponse

# --- Facade para o Serviço de LLM ---
analyze_context_with_llm = analyze_context_with_llm_real

# --- Facade para o K-Search ---
class KnowledgeSuggestion(BaseModel):
    title: str
    summary: str
    score: float 
    source: str
    link: str

MOCK_SUGGESTIONS = [
    KnowledgeSuggestion(
        title="Guia V3",
        summary="Doc de migração...",
        score=95.0,
        source="Confluence",
        link="#"
    )
]

async def find_relevant_document(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    try:
        return await find_relevant_document_real(query_text, top_k)
    except Exception as e:
        print(f"K-Search fallback: {e}")
        return [s.model_dump() for s in MOCK_SUGGESTIONS]

async def analyze_skills_with_llm(context_summary: str) -> Optional[SkillSuggestionsResponse]:
    # Placeholder para evitar quebras se chamado
    return None