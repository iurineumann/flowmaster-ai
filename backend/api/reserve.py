# backend/api/reserve.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
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
    return f"reserva_sugestao:{user_id}"

router = APIRouter()

class ReservationSuggestion(BaseModel):
    is_suggested: bool
    resource_name: str
    time_slot: Optional[str] = None
    reason: str

@router.get("/sugestao", response_model=ReservationSuggestion)
@cached(
    ttl=1800,
    key_builder=cache_key_builder,
    cache=RedisCache,
    endpoint=os.environ.get('REDIS_ENDPOINT', "redis"),
    port=6379
)
async def get_reservation_suggestion(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_real_access_token),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    critical_item = await context_service.get_critical_context(user_id, access_token) 
    
    if not critical_item:
        return ReservationSuggestion(
            is_suggested=False,
            resource_name="N/A",
            reason="Nenhum foco crítico detectado para sugerir reserva."
        ).model_dump()

    urgency_score_simulated = 98 
    
    if urgency_score_simulated >= 90:
        next_hour = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        
        dispatch_event({
            "event_type": "resource_reservation_suggested",
            "payload": {
                "user_id": user_id,
                "resource": "Sala de Foco 1A",
                "time": next_hour
            }
        })
        
        return ReservationSuggestion(
            is_suggested=True,
            resource_name="Sala de Foco 1A (Sala Silenciosa)",
            time_slot=f"A partir das {next_hour}",
            reason="Foco Crítico de Pagamento detectado. Reserva de recurso para concentração recomendada."
        ).model_dump()
    else:
        return ReservationSuggestion(
            is_suggested=False,
            resource_name="N/A",
            reason="O foco de trabalho atual não exige uma reserva de recurso imediata."
        ).model_dump()