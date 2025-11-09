# backend/api/reserve.py
from fastapi import APIRouter
from typing import Optional
from ..reserve_agent import ReserveAgent, ReserveSuggestionModel

router = APIRouter()

@router.get("/suggestion/{project_tag}", response_model=Optional[ReserveSuggestionModel])
def get_reserve_suggestion(project_tag: str):
    """
    Endpoint que usa o Agente Reserva Inteligente para sugerir um recurso físico.
    """
    # Hardcoded user_id para PoC
    user_id = 42
    
    reserve_agent = ReserveAgent(user_id=user_id)
    suggestion = reserve_agent.get_suggestion(current_focus_tag=project_tag)
    
    return suggestion