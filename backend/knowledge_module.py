# backend/knowledge_module.py

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Serviços Reais
from .services.llm_service import analyze_context_with_llm_real
from .services.vector_db_service import vector_db # Singleton seguro
from .services.data_security import security_service

logger = logging.getLogger(__name__)

# --- Facade para o Serviço de LLM ---
analyze_context_with_llm = analyze_context_with_llm_real

class KnowledgeSuggestion(BaseModel):
    title: str
    summary: str
    score: float 
    source: str
    link: str

async def find_relevant_document(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Executa busca semântica no acervo de conhecimento da empresa.
    """
    try:
        if not query_text:
            return []

        # 1. Sanitização (LGPD) - Remove CPF/Email antes de buscar/logar
        safe_query = security_service.mask_sensitive_data(query_text)
        logger.info(f"🔍 [RAG] Buscando por: {safe_query}")

        # 2. Busca Vetorial (ChromaDB)
        # O vector_db_service já deve estar inicializado com FileLock
        if not vector_db:
            logger.warning("⚠️ [RAG] Banco vetorial não disponível.")
            return []

        results = await vector_db.search_relevant(safe_query, top_k)
        
        # 3. Formatação
        formatted = []
        for doc in results:
            meta = doc.get('metadata', {})
            formatted.append({
                "title": meta.get('title', 'Documento Interno'),
                "summary": doc.get('content', '')[:300] + "...",
                "score": float(doc.get('score', 0)),
                "source": meta.get('source', 'Base de Conhecimento'),
                "link": meta.get('url', '#')
            })
            
        return formatted

    except Exception as e:
        logger.error(f"❌ [RAG] Erro na busca: {e}")
        # Fallback silencioso para não quebrar a UI
        return []

# Mantido para compatibilidade com chamadas legadas
async def analyze_skills_with_llm(context_summary: str) -> Optional[Any]:
    return None