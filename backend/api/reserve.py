# backend/api/reserve.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from aiocache import cached
from ..reserve_agent import ReserveAgent

router = APIRouter()

class ReservationSuggestion(BaseModel):
    is_suggested: bool
    resource_name: Optional[str] = None
    time_slot: Optional[str] = None
    reason: Optional[str] = None

@router.get("/sugestao", response_model=ReservationSuggestion)
@cached(ttl=300)
async def get_reservation_suggestion(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = ReserveAgent(db)
        suggestion = await agent.process(user.id)
        
        # ✅ CORREÇÃO CRÍTICA: Converter para Dict
        if hasattr(suggestion, "model_dump"):
            return suggestion.model_dump()
        if hasattr(suggestion, "dict"):
            return suggestion.dict()
            
        return suggestion

    except Exception as e:
        print(f"❌ [Reserve API] Erro: {e}")
        return {
            "is_suggested": False, 
            "reason": "Indisponível no momento"
        }