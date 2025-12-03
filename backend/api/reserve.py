# backend/api/reserve.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
# Import do Cache
from ..utils.multi_layer_cache import cache_decorator as cached
# Import do Agente
from ..reserve_agent import ReserveAgent

router = APIRouter()

class ReservationSuggestion(BaseModel):
    is_suggested: bool
    resource_name: Optional[str] = None
    time_slot: Optional[str] = None
    reason: Optional[str] = None

@router.get("/sugestao", response_model=ReservationSuggestion)
# O cache precisa que o retorno seja serializável (Dict), não objeto Pydantic
@cached(key_prefix="reserva_sugestao", ttl=300)
async def get_reservation_suggestion(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = ReserveAgent(db)
        suggestion = await agent.check_and_suggest_reservation(user.id)
        
        # O agente retorna um Dict ou um Objeto? Vamos garantir que seja compatível.
        # Se suggestion já for dict, ótimo. Se for modelo, convertemos.
        if hasattr(suggestion, "model_dump"):
            return suggestion.model_dump() # ✅ Pydantic v2
        if hasattr(suggestion, "dict"):
            return suggestion.dict() # ✅ Pydantic v1
            
        # Se já for dict ou compatível
        return suggestion

    except Exception as e:
        print(f"Erro no ReserveAgent: {e}")
        # Retorna dict vazio/nulo em caso de erro para não quebrar o front
        return {
            "is_suggested": False, 
            "reason": "Indisponível no momento"
        }