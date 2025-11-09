# backend/api/reserve.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from cachetools import cached, TTLCache

# --- Modelos Pydantic para a Resposta da API ---
# Cache de 60 segundos
AGENT_DATA_CACHE = TTLCache(maxsize=128, ttl=60) 

def agent_cache_key(user_id: int) -> int:
    return user_id

class ReserveAgentData(BaseModel):
    """
    Modelo da resposta principal do Agente Reserva, sugerindo uma ação 
    e fornecendo um link, se necessário.
    """
    suggestion: str
    action_required: bool
    link_to_map: Optional[str] = None # Link para o SGP - Mapa de Reservas

# --- Roteador FastAPI ---

router = APIRouter()

@router.get("/sugestao/{user_id}", response_model=ReserveAgentData)
@cached(AGENT_DATA_CACHE, key=agent_cache_key)
def get_reservation_suggestion(user_id: int):
    """
    Endpoint que sugere a reserva de um recurso (Focus Room, Sala de Reunião, etc.)
    com base no contexto de alta demanda do usuário.
    """
    
    # 📝 Simulação da Lógica de IA: 
    # Contexto Base: Assumimos que o Agente de Contexto detectou um foco crítico 
    # (ex: o BUG CRÍTICO do CLIENTE_X), indicando alta necessidade de foco.
    
    is_critical_context = True 
    
    if is_critical_context:
        suggestion = "Seu foco atual requer **concentração máxima**. Sugestão: Reserve uma **Focus Room** por 2h a partir de agora."
        action_required = True
        # Usamos o link do SGP-Mapa de reservas mencionado anteriormente
        link_to_map = "https://sistemas.t2mlab.com/officefloorplan" 
    else:
        suggestion = "Seu agendamento está em dia. Nenhuma reserva de recurso crítica sugerida."
        action_required = False
        link_to_map = None

    return ReserveAgentData(
        suggestion=suggestion,
        action_required=action_required,
        link_to_map=link_to_map
    )