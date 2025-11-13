# backend/api/reserve.py (CORRIGIDO O IMPORT)

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from aiocache import cached
from datetime import datetime, timedelta

from ..utils.security import get_current_user_id, get_access_token_mock # ✅ CORREÇÃO AQUI
from ..utils.event_dispatcher import dispatch_event
from ..services.context_data_service import ContextDataService, get_context_data_service

# --- Configuração de Cache ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
RESERVE_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 1800
}

router = APIRouter()

class ReservationSuggestion(BaseModel):
# ... (O corpo da classe ReservationSuggestion permanece o mesmo)
    is_suggested: bool
    resource_name: str
    time_slot: Optional[str] = None
    reason: str

@router.get("/sugestao", response_model=ReservationSuggestion)
@cached(
    CACHE_BACKEND, 
    key_builder=lambda user_id, access_token, context_service: user_id,
    **RESERVE_CACHE_KWARGS
)
async def get_reservation_suggestion(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    critical_item = await context_service.get_critical_context(user_id, access_token) 
    
    if not critical_item:
        return ReservationSuggestion(
            is_suggested=False,
            resource_name="N/A",
            reason="Nenhum foco crítico detectado para sugerir reserva."
        )

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
            reason=f"Foco Crítico de Pagamento detectado. Reserva de recurso para concentração recomendada. Detalhe: {critical_item.subject_or_title}"
        )
    else:
        return ReservationSuggestion(
            is_suggested=False,
            resource_name="N/A",
            reason="O foco de trabalho atual não exige uma reserva de recurso imediata."
        )