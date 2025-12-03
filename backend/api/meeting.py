# backend/api/meeting.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from ..utils.multi_layer_cache import cache_decorator as cached
# ✅ Usa o novo agente
from ..meeting_agent import MeetingAgent

router = APIRouter()

class MeetingSuggestion(BaseModel):
    is_required: bool
    title: str = Field(description="Título sugerido da reunião.")
    duration_minutes: int
    suggested_agenda: List[str]
    context_source: str

@router.get("/sugestao", response_model=MeetingSuggestion)
@cached(key_prefix="meeting_sugestao", ttl=300)
async def get_meeting_suggestion(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = MeetingAgent(db)
        suggestion = await agent.process(user.id)
        
        # Garante serialização para o Cache e Frontend
        if hasattr(suggestion, "model_dump"):
            return suggestion.model_dump()
        
        return suggestion

    except Exception as e:
        print(f"❌ [Meeting API] Erro: {e}")
        return {
            "is_required": False,
            "title": "Serviço Indisponível",
            "duration_minutes": 0,
            "suggested_agenda": [],
            "context_source": "Erro no sistema"
        }