# backend/api/skill.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from aiocache import cached
from aiocache.backends.redis import RedisCache

from ..utils.security import get_current_user_id, get_graph_token # ✅ CORREÇÃO
from ..utils.event_dispatcher import dispatch_event, SkillGapIdentifiedEvent
from ..llm_optimization import SkillSuggestionsResponse
from ..services.context_data_service import ContextDataService, get_context_data_service
from ..knowledge_module import analyze_skills_with_llm

def cache_key_builder(func, *args, **kwargs):
    user_id = kwargs.get('user_id')
    return f"skill_sugestoes:{user_id}"

router = APIRouter()

@router.get("/sugestoes", response_model=SkillSuggestionsResponse)
@cached(
    ttl=6 * 3600,
    key_builder=cache_key_builder,
    cache=RedisCache,
    endpoint=os.environ.get('REDIS_ENDPOINT', "redis"),
    port=6379
)
async def get_skill_suggestions(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_graph_token), # ✅ CORREÇÃO
    context_service: ContextDataService = Depends(get_context_data_service)
):
    critical_item = await context_service.get_critical_context(user_id, access_token)
    
    if not critical_item:
        return SkillSuggestionsResponse(suggestions=[])
        
    problema_detalhado = critical_item.content_preview 

    suggestions = await analyze_skills_with_llm(problema_detalhado) 
    
    if not suggestions:
        return SkillSuggestionsResponse(suggestions=[])

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