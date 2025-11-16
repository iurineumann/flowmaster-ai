# backend/api/meeting.py

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from aiocache import cached
from aiocache.backends.redis import RedisCache
from datetime import datetime, timedelta

from ..utils.security import get_current_user_id
from backend.services.graph_repository import get_real_access_token
from ..services.context_data_service import ContextDataService, get_context_data_service
from ..utils.event_dispatcher import dispatch_event

# --- Configuração de Cache (Padronizado) ---
def cache_key_builder(func, *args, **kwargs):
    user_id = kwargs.get('user_id')
    return f"meeting_sugestao:{user_id}"

router = APIRouter()

class MeetingSuggestion(BaseModel):
    is_required: bool
    title: str = Field(description="Título sugerido da reunião (Ex: Daily Sync Foco Cripto V3).")
    duration_minutes: int
    suggested_agenda: List[str]
    context_source: str

@router.get("/sugestao", response_model=MeetingSuggestion)
@cached(
    ttl=3600,
    key_builder=cache_key_builder,
    cache=RedisCache,
    endpoint=os.environ.get('REDIS_ENDPOINT', "redis"),
    port=6379
)
async def get_meeting_suggestion(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_real_access_token),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    critical_item = await context_service.get_critical_context(user_id, access_token) 

    if critical_item:
        problema_detalhado = critical_item.content_preview 

        if "criptografia" in problema_detalhado.lower():
            pauta = ["Revisão do Log de Erros do Gateway Alpha", "Decisão sobre Rollback ou Hotfix V3", "Alocação de Recurso Sênior"]
            titulo = f"🔥 Emergency Session: Hotfix {critical_item.project_tag} - Cripto V3"
            
            dispatch_event({
                "event_type": "meeting_suggested",
                "payload": {"user_id": user_id, "title": titulo, "pauta": pauta}
            })
            
            return MeetingSuggestion(
                is_required=True,
                title=titulo,
                duration_minutes=30,
                suggested_agenda=pauta,
                context_source=f"Detectado em comunicações recentes."
            ).model_dump()

    return MeetingSuggestion(
        is_required=False,
        title="Nenhuma Reunião Imediata Necessária",
        duration_minutes=0,
        suggested_agenda=[],
        context_source="O foco de trabalho atual não exige uma reunião emergencial."
    ).model_dump()