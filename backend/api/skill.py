# backend/api/skill.py (CORRIGIDO O IMPORT)

import os
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from aiocache import cached

from ..utils.security import get_current_user_id, get_access_token_mock # ✅ CORREÇÃO AQUI
from ..utils.event_dispatcher import dispatch_event, SkillGapIdentifiedEvent
from ..llm_optimization import SkillSuggestionsResponse, SkillSuggestionItem
from ..services.context_data_service import ContextDataService, get_context_data_service

# --- Configuração de Cache ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
SKILL_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 6 * 3600
}

router = APIRouter()

async def analyze_skills_with_llm(context_summary: str) -> SkillSuggestionsResponse:
# ... (O corpo da função analyze_skills_with_llm permanece o mesmo)
    return SkillSuggestionsResponse(suggestions=[
        SkillSuggestionItem(
            title="Criptografia V3: Guia de Migração PCI-DSS", 
            relevance_score=95
        ),
        SkillSuggestionItem(
            title="Debugging de Erros 500 em Gateways de Pagamento", 
            relevance_score=88
        ),
    ])

@router.get("/sugestoes", response_model=SkillSuggestionsResponse)
@cached(
    CACHE_BACKEND, 
    key_builder=lambda user_id, access_token, context_service: user_id,
    **SKILL_CACHE_KWARGS
)
async def get_skill_suggestions(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    critical_item = await context_service.get_critical_context(user_id, access_token)
    
    if not critical_item:
        return SkillSuggestionsResponse(suggestions=[])
        
    problema_detalhado = critical_item.content_preview 

    suggestions = await analyze_skills_with_llm(problema_detalhado) 
    
    if suggestions.suggestions:
        dispatch_event(SkillGapIdentifiedEvent(payload={
            "user_id": user_id, 
            "focus": problema_detalhado,
            "suggestions": [s.title for s in suggestions.suggestions]
        }))

    return suggestions