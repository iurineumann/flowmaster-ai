# backend/api/skill.py (CONTEÚDO COMPLETO E CORRIGIDO PARA O AUTH REAL)

from fastapi import APIRouter, Depends 
from typing import Dict, Any, List
from cachetools import TTLCache 

# IMPORTS
from ..knowledge_module import analyze_skills_with_llm # Funcao de skills
from ..utils.security import get_current_user_id 
# ✅ CORREÇÃO CRÍTICA: Mudar para get_real_access_token
from ..services.graph_repository import get_real_access_token, GraphRepository 
from ..llm_optimization import SkillSuggestionsResponse # Schema de resposta

# Configuração de Cache
SKILL_DATA_CACHE = TTLCache(maxsize=128, ttl=300) # 5 minutos de cache

router = APIRouter()
repo = GraphRepository()

@router.get("/sugestoes", response_model=Dict[str, Any])
# Em produção, você adicionaria o decorator de cache aqui:
# @cached(SKILL_DATA_CACHE, key=lambda user_id, access_token: user_id) 
async def get_skill_suggestions(
    user_id: int = Depends(get_current_user_id),
    # ✅ CORREÇÃO CRÍTICA: Usar a dependência de Token REAL
    access_token: str = Depends(get_real_access_token) 
):
    """
    Endpoint para buscar sugestões de skills com base no contexto crítico atual.
    """
    
    # 1. Obter o contexto bruto (o mesmo usado pelo Context Agent)
    all_raw_data = await repo.get_raw_context_by_user(user_id, access_token)
    
    # Lógica de Foco Crítico (Simulando o mesmo foco do Context Agent)
    foco_critico_tag = "CLIENTE_X"
    itens_do_foco = [item for item in all_raw_data if item.project_tag == foco_critico_tag]
    
    if not itens_do_foco:
        # Se não houver contexto crítico, retorne uma lista vazia ou genérica
        return {
            "user_id": user_id,
            "contexto": "Nenhum foco crítico identificado no momento.",
            "sugestoes": []
        }

    problema_detalhado = itens_do_foco[0].content_preview 
    
    # 2. Chamada ao Serviço de LLM para Skills (assíncrona)
    skill_suggestions_data = await analyze_skills_with_llm(problema_detalhado) 
    
    # 3. Retorno da API
    return {
        "user_id": user_id,
        "contexto": "Sugestões baseadas no foco principal: " + (skill_suggestions_data.suggestions[0].title if skill_suggestions_data.suggestions else "Indisponível."),
        "sugestoes": skill_suggestions_data.model_dump().get("suggestions", [])
    }