# backend/api/meeting.py (CORRIGIDO O IMPORT)

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from aiocache import cached
from datetime import datetime, timedelta

from ..utils.security import get_current_user_id, get_access_token_mock # ✅ CORREÇÃO AQUI
from ..utils.event_dispatcher import dispatch_event
from ..services.context_data_service import ContextDataService, get_context_data_service

# --- Configuração de Cache ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
MEETING_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 3600
}

router = APIRouter()

class MeetingSuggestion(BaseModel):
# ... (O corpo da classe MeetingSuggestion permanece o mesmo)
    is_required: bool
    title: str = Field(description="Título sugerido da reunião.")
    duration_minutes: int
    suggested_agenda: List[str]
    context_source: str

@router.get("/sugestao", response_model=MeetingSuggestion)
@cached(
    CACHE_BACKEND, 
    key_builder=lambda user_id, access_token, context_service: user_id,
    **MEETING_CACHE_KWARGS
)
async def get_meeting_suggestion(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock),
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
                context_source=f"Detectado no foco {critical_item.project_tag}."
            )

    return MeetingSuggestion(
        is_required=False,
        title="N/A",
        duration_minutes=0,
        suggested_agenda=[],
        context_source="Nenhum contexto crítico encontrado para agendar reunião."
    )