# backend/api/skill.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from aiocache import cached

from ..utils.security import get_current_user_id, get_access_token_mock
from ..utils.event_dispatcher import dispatch_event, SkillGapIdentifiedEvent
from ..llm_optimization import SkillSuggestionsResponse, SkillSuggestionItem
from ..services.context_data_service import ContextDataService, get_context_data_service

# --- Configuração de Cache (Padronizado) ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
SKILL_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
}

def cache_key_builder_user_only(func_args, func_kwargs):
    user_id = func_kwargs.get('user_id', func_args[0] if func_args else None)
    return f"{func_kwargs['self'].__class__.__name__}:{func_kwargs['func'].__name__}:{user_id}"

router = APIRouter()

async def analyze_skills_with_llm(context_summary: str) -> SkillSuggestionsResponse:
    print(f"🧠 [LLM-SKILL] Iniciando análise de skill para: '{context_summary[:50]}...'")
    
    llm_output_json = {
        "suggestions": [
            {
                "title": "Migração para Protocolo V3 de Criptografia (Curso)",
                "relevance_score": 95
            },
            {
                "title": "Melhores Práticas de PCI DSS para APIs de Pagamento",
                "relevance_score": 88
            },
            {
                "title": "Debugging Assíncrono com FastAPI e Uvicorn",
                "relevance_score": 75
            }
        ]
    }
    
    try:
        return SkillSuggestionsResponse.model_validate(llm_output_json)
    except Exception as e:
        print(f"❌ [LLM-SKILL-PARSE] Falha ao validar o JSON da LLM: {e}")
        return SkillSuggestionsResponse(
            suggestions=[SkillSuggestionItem(title="Revisão de Criptografia Básica", relevance_score=50)]
        )

@router.get("/sugestoes", response_model=SkillSuggestionsResponse)
@cached(
    CACHE_BACKEND, 
    ttl=6 * 3600, # TTL de 6 horas
    key_builder=cache_key_builder_user_only,
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
        dispatch_event(
            SkillGapIdentifiedEvent(
                payload={
                    "user_id": user_id,
                    "focus": problema_detalhado,
                    "top_skill": suggestions.suggestions[0].title
                }
            )
        )

    return suggestions