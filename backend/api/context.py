# backend/api/context.py

from fastapi import APIRouter, Depends 
from typing import Dict, Any, Callable, Optional
import os 
from aiocache import cached, Cache
from aiocache.backends.redis import RedisCache

from ..knowledge_module import find_relevant_document, analyze_context_with_llm
# ✅ CORREÇÃO: Importa o novo get_graph_token (com scope) e o mock
from ..utils.security import get_current_user_id, get_graph_token
from ..utils.event_dispatcher import dispatch_event, CriticalContextDetectedEvent
from ..utils.ws_manager import manager 
from ..services.context_data_service import ContextDataService, get_context_data_service 

# --- Configuração de Cache ---
def cache_key_builder(func, *args, **kwargs):
    user_id = kwargs.get('user_id')
    return f"context_agregado:{user_id}"

router = APIRouter()

DEFAULT_LLM_RESPONSE = {
    "focus_title": "N/A (LLM Indisponível)",
    "summary_analysis": "Serviço de IA indisponível. Não foi possível analisar o contexto.",
    "urgency_score": 0,
    "technical_tags": []
}

@router.get("/agregado", response_model=Dict[str, Any])
@cached(
    ttl=60, 
    key_builder=cache_key_builder,
    cache=RedisCache,
    endpoint=os.environ.get('REDIS_ENDPOINT', "redis"),
    port=6379
)
async def get_user_context_agregado(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_graph_token), # ✅ CORREÇÃO: Usa o token com scope de Graph
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
    
    sugestoes_conhecimento = await find_relevant_document( 
        query_text=problema_detalhado, 
        top_k=2
    )
    
    if not summary_data:
        return {
            "user_id": user_id,
            "foco_critico": foco_critico_tag,
            "foco_detalhe": problema_detalhado,
            "resumo_llm": DEFAULT_LLM_RESPONSE,
            "urgencia": 0,
            "sugestoes_conhecimento": sugestoes_conhecimento
        }

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
    
    return {
        "user_id": user_id,
        "foco_critico": foco_critico_tag,
        "foco_detalhe": problema_detalhado,
        "resumo_llm": summary_data.model_dump(),
        "urgencia": summary_data.urgency_score,
        "sugestoes_conhecimento": sugestoes_conhecimento
    }