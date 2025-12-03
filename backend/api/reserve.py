# backend/api/reserve.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from ..utils.multi_layer_cache import cache_decorator as cached
from ..reserve_agent import ReserveAgent

router = APIRouter()

class ReservationSuggestion(BaseModel):
    is_suggested: bool
    resource_name: Optional[str] = None
    time_slot: Optional[str] = None
    reason: Optional[str] = None

@router.get("/sugestao", response_model=ReservationSuggestion)
@cached(key_prefix="reserva_sugestao", ttl=300)
async def get_reservation_suggestion(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = ReserveAgent(db)
        # ✅ Chama o método 'process' que implementamos no Agente Real
        suggestion = await agent.process(user.id)
        
        # ✅ Serialização manual para garantir compatibilidade com Cache JSON
        if hasattr(suggestion, "model_dump"):
            return suggestion.model_dump()
        if isinstance(suggestion, dict):
            return suggestion
            
        return suggestion

    except Exception as e:
        print(f"❌ [Reserve API] Erro: {e}")
        return {
            "is_suggested": False, 
            "reason": "Serviço indisponível no momento"
        }