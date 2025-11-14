# backend/api/context.py

from fastapi import APIRouter, Depends 
from typing import Dict, Any, Callable
import os 
from aiocache import cached

from ..services.graph_repository import get_access_token_mock
from ..knowledge_module import find_relevant_document, analyze_context_with_llm
from ..utils.security import get_current_user_id 
from ..utils.event_dispatcher import dispatch_event, CriticalContextDetectedEvent
from ..utils.ws_manager import manager 
from ..services.context_data_service import ContextDataService, get_context_data_service

# --- Configuração de Cache (Padronizado) ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
}

def cache_key_builder_user_only(func_args, func_kwargs):
    # Usa o user_id (primeiro arg depois de self/cls, ou kwarg)
    user_id = func_kwargs.get('user_id', func_args[0] if func_args else None)
    return f"{func_kwargs['self'].__class__.__name__}:{func_kwargs['func'].__name__}:{user_id}"

router = APIRouter()
repo = GraphRepository()

@router.get("/agregado", response_model=Dict[str, Any])
@cached(
    ttl=60, # TTL de 1 minuto para dados de contexto
    key_builder=cache_key_builder_user_only,
    cache=CACHE_BACKEND,
    **CACHE_KWARGS
)
async def get_user_context_agregado(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    critical_item = await context_service.get_critical_context(user_id, access_token) 
    
    if not critical_item:
        return { 
            "user_id": user_id,
            "foco_critico": "Nenhum Foco Crítico",
            "foco_detalhe": "Nenhuma crise detectada no momento.",
            "resumo_llm": {
                "focus_title": "Operação Normal",
                "summary_analysis": "Nenhuma crise detectada.",
                "urgency_score": 0,
                "technical_tags": []
            },
            "urgencia": 0,
            "sugestoes_conhecimento": []
        }

    problema_detalhado = critical_item.content_preview 
    foco_critico_tag = critical_item.project_tag
    
    summary_data = await analyze_context_with_llm(problema_detalhado) 
    
    critical_event = CriticalContextDetectedEvent(
        payload={
            "user_id": user_id,
            "project": foco_critico_tag,
            "detail": summary_data.summary_analysis
        }
    )
    dispatch_event(critical_event)
    
    if summary_data.urgency_score >= 90:
        notification_message = {
            "type": "CRITICAL_BUG_ALERT",
            "title": summary_data.focus_title,
            "urgency": summary_data.urgency_score,
            "detail": summary_data.summary_analysis
        }
        await manager.send_personal_message(notification_message, user_id)
    
    sugestoes_conhecimento = await find_relevant_document( 
        query_text=problema_detalhado, 
        top_k=2
    )
    
    return {
        "user_id": user_id,
        "foco_critico": foco_critico_tag,
        "foco_detalhe": problema_detalhado,
        "resumo_llm": summary_data.model_dump(),
        "urgencia": summary_data.urgency_score,
        "sugestoes_conhecimento": sugestoes_conhecimento
    }