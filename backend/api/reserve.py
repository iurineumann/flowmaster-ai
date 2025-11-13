# backend/api/reserve.py (VERSÃO FINAL COM ASYNC E INTEGRAÇÃO)

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from cachetools import cached, TTLCache 
from datetime import datetime, timedelta

# IMPORTS
from ..utils.security import get_access_token_mock, get_current_user_id
from ..services.graph_repository import  GraphRepository 
from ..utils.event_dispatcher import dispatch_event # Pode disparar eventos de reserva futura

router = APIRouter()

# Configuração de Cache
RESERVE_CACHE = TTLCache(maxsize=128, ttl=1800) # Cache de 30 minutos

repo = GraphRepository()

# --- Modelos Pydantic ---
class ReservationSuggestion(BaseModel):
    is_suggested: bool
    resource_name: str
    time_slot: Optional[str] = None
    reason: str

# --- Endpoint do Agente de Reserva ---

@router.get("/sugestao", response_model=ReservationSuggestion)
@cached(RESERVE_CACHE, key=lambda user_id, token: user_id)
async def get_reservation_suggestion(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock)
):
    """
    Sugere a reserva de um recurso (ex: Sala de Foco) se o contexto for crítico.
    """
    # 1. Busca Dados (Assíncrono)
    all_raw_data = await repo.get_raw_context_by_user(user_id, access_token)
    
    foco_critico_tag = "CLIENTE_X"
    itens_do_foco = [item for item in all_raw_data if item.project_tag == foco_critico_tag]
    
    if not itens_do_foco:
        return ReservationSuggestion(
            is_suggested=False,
            resource_name="N/A",
            reason="Nenhum foco crítico detectado para sugerir reserva."
        )

    # 2. Simulação de Análise de Urgência
    # Em um sistema real, essa urgência viria do Agente de Contexto (summary_data.urgency_score)
    # Usaremos um threshold de 90 para a tag CLIENTE_X.
    urgency_score_simulated = 98 
    
    if urgency_score_simulated >= 90:
        # 3. Sugestão de Reserva
        next_hour = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        
        # Disparo de Evento (Simulação de Ação Futura)
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
        )
    else:
        return ReservationSuggestion(
            is_suggested=False,
            resource_name="N/A",
            reason="Nenhum foco de trabalho com urgência suficiente para reserva automática."
        )