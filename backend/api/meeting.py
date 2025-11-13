# backend/api/meeting.py (NOVO AGENTE)

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from cachetools import cached, TTLCache
from datetime import datetime, timedelta

from ..utils.security import get_access_token_mock, get_current_user_id
from ..services.graph_repository import GraphRepository 
from ..utils.event_dispatcher import dispatch_event

router = APIRouter()
MEETING_CACHE = TTLCache(maxsize=128, ttl=3600) # Cache de 1 hora

class MeetingSuggestion(BaseModel):
    is_required: bool
    title: str = Field(description="Título sugerido da reunião (Ex: Daily Sync Foco Cripto V3).")
    duration_minutes: int
    suggested_agenda: List[str]
    context_source: str

@router.get("/sugestao", response_model=MeetingSuggestion)
@cached(MEETING_CACHE, key=lambda user_id, token: user_id)
async def get_meeting_suggestion(
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock)
):
    """
    Sugere pauta e reunião com base no foco de trabalho crítico.
    """
    repo = GraphRepository()
    all_raw_data = await repo.get_raw_context_by_user(user_id, access_token)
    
    foco_critico_tag = "CLIENTE_X"
    itens_do_foco = [item for item in all_raw_data if item.project_tag == foco_critico_tag]

    if itens_do_foco:
        problema_detalhado = itens_do_foco[0].content_preview 

        # 🧠 Simulação de Chamada LLM para Pauta (Em produção, usaria um prompt otimizado)
        if "criptografia" in problema_detalhado.lower():
            pauta = ["Revisão do Log de Erros do Gateway Alpha", "Decisão sobre Rollback ou Hotfix V3", "Alocação de Recurso Sênior"]
            titulo = f"🔥 Emergency Session: Hotfix {foco_critico_tag} - Cripto V3"
            
            # Dispara evento de agendamento sugerido
            dispatch_event({
                "event_type": "meeting_suggested",
                "payload": {"user_id": user_id, "title": titulo, "pauta": pauta}
            })
            
            return MeetingSuggestion(
                is_required=True,
                title=titulo,
                duration_minutes=30,
                suggested_agenda=pauta,
                context_source=f"Detectado em {len(itens_do_foco)} comunicações recentes."
            )

    return MeetingSuggestion(
        is_required=False,
        title="Nenhuma Reunião Imediata Necessária",
        duration_minutes=0,
        suggested_agenda=[],
        context_source="O foco de trabalho atual não exige uma reunião emergencial."
    )