# backend/api/context.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from aiocache import cached

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from ..context_agent import ContextAgent
from ..services.context_data_service import ContextDataService

router = APIRouter()

class ContextoAgregadoResponse(BaseModel):
    usuario: str
    funcao: str
    projeto_atual: str  # Será preenchido pelo "Focus" da IA
    sprint_atual: str   # Será preenchido pela "Sprint" da IA
    tarefas_pendentes: int
    proxima_reuniao: Optional[str] = None
    alertas: List[str] = []

@router.get("/agregado", response_model=ContextoAgregadoResponse)
@cached(ttl=300) # Cache de 5 min para não sobrecarregar a LLM
async def get_contexto_agregado(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. Coleta dados brutos para contagem
        data_service = ContextDataService(db)
        raw_context = await data_service.get_aggregated_context(user.id)
        task_count = raw_context.get("task_count", 0)
        
        # 2. Aciona o Agente Inteligente
        agent = ContextAgent(db)
        analysis = await agent.analyze_user_focus(user.id)
        
        # 3. Monta resposta
        response = ContextoAgregadoResponse(
            usuario=user.full_name or user.email,
            funcao="Engenheiro de Software", # Exemplo fixo ou vindo de config
            projeto_atual=analysis.get("focus", "Explorando Projetos"),
            sprint_atual=analysis.get("sprint", "Sprint Atual"),
            tarefas_pendentes=task_count,
            proxima_reuniao=None, # Implementar Graph depois
            alertas=analysis.get("alerts", [])
        )

        return response.model_dump()

    except Exception as e:
        print(f"❌ [Context API] Erro: {e}")
        # Fallback de segurança
        return {
            "usuario": user.full_name or "Usuário",
            "funcao": "N/A",
            "projeto_atual": "Sistema Indisponível",
            "sprint_atual": "-",
            "tarefas_pendentes": 0,
            "proxima_reuniao": None,
            "alertas": ["Erro ao carregar contexto"]
        }