# backend/api/context.py (CORRIGIDO O IMPORT)

import os
from fastapi import APIRouter, Depends 
from typing import Dict, Any, Callable
from aiocache import cached

from ..services.context_data_service import ContextDataService, get_context_data_service 
from ..knowledge_module import find_relevant_document, analyze_context_with_llm
from ..utils.security import get_current_user_id, get_access_token_mock # ✅ CORREÇÃO AQUI
from ..utils.event_dispatcher import dispatch_event, CriticalContextDetectedEvent
from ..utils.ws_manager import manager 

# --- Configuração de Cache ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
CONTEXT_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 60
}

def cache_key_for_user_context_agregado(user_id: int, access_token: str) -> str:
    return f"user_context_agregado_id:{user_id}"

router = APIRouter()
# ... (O restante do código do endpoint get_user_context_agregado permanece o mesmo)
@router.get("/agregado", response_model=Dict[str, Any])
@cached(
    CACHE_BACKEND, 
    key_builder=cache_key_for_user_context_agregado,
    **CONTEXT_CACHE_KWARGS
)
async def get_user_context_agregado(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock),
    context_service: ContextDataService = Depends(get_context_data_service) 
):
    critical_item = await context_service.get_critical_context(user_id, access_token) 
    # ... (Resto da função)
    if not critical_item:
        return { 
            "user_id": user_id,
            "foco_critico": "Nenhum Foco Crítico",
            "resumo_ia": "Nenhuma crise detectada no momento. Tudo está operando normalmente.",
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
        "resumo_ia": summary_data.summary_analysis,
        "titulo_foco": summary_data.focus_title,
        "tags_tecnicas": summary_data.technical_tags,
        "urgencia": summary_data.urgency_score,
        "sugestoes_conhecimento": sugestoes_conhecimento
    }