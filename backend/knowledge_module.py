# backend/knowledge_module.py

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Imports de Serviços Reais
from .services.llm_service import analyze_context_with_llm_real
from .services.vector_db_service import vector_db
from .utils.data_security import security_service

logger = logging.getLogger(__name__)

# --- Facade para o Serviço de LLM (Compatibilidade) ---
analyze_context_with_llm = analyze_context_with_llm_real

# --- Facade para o RAG (Knowledge Search) ---
class KnowledgeSuggestion(BaseModel):
    title: str
    summary: str
    score: float 
    source: str
    link: str

async def find_relevant_document(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Executa o pipeline RAG: Sanitização -> Busca Vetorial.
    """
    try:
        # 1. Sanitização da Query (LGPD)
        # Remove dados sensíveis antes de enviar para o embedding model ou logar
        safe_query = security_service.mask_sensitive_data(query_text)
        
        logger.info(f"🔍 [Knowledge] Buscando por: {safe_query}")

        # 2. Busca no Banco Vetorial
        results = await vector_db.search_relevant(safe_query, top_k)
        
        # 3. Formatação dos Resultados
        formatted_results = []
        for res in results:
            meta = res.get('metadata', {})
            formatted_results.append({
                "title": meta.get('title', 'Documento Sem Título'),
                "summary": res.get('content', '')[:200] + "...", # Preview
                "score": float(res.get('score', 0)),
                "source": meta.get('source', 'Knowledge Base'),
                "link": meta.get('url', '#')
            })
            
        return formatted_results

    except Exception as e:
        logger.error(f"❌ [Knowledge] Erro no pipeline RAG: {e}")
        return [] # Retorna lista vazia (graceful degradation)

# Mantido para compatibilidade com imports legados, se houver
async def analyze_skills_with_llm(context_summary: str) -> Optional[Any]:
    return None