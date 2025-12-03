# backend/api/skill.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
# Importar o agente real
from ..skill_agent import SkillAgent

router = APIRouter()

class SkillItem(BaseModel):
    skill: str
    relevancia: str
    motivo: str

class SkillSuggestionsResponse(BaseModel):
    sugestoes: List[SkillItem]

@router.get("/sugestoes", response_model=SkillSuggestionsResponse)
async def get_skill_suggestions(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Instancia o Agente Real
        agent = SkillAgent(db)
        
        # O agente analisa o perfil do usuário (Tasks, Histórico) e sugere skills
        # Se o agente falhar (ex: LLM offline), ele deve ter um fallback interno
        sugestoes_raw = await agent.analyze_user_context(user.id)
        
        # Mapeia para o modelo de resposta
        return SkillSuggestionsResponse(
            sugestoes=[
                SkillItem(
                    skill=s.get("name", "Skill"),
                    relevancia=s.get("relevance", "Média"),
                    motivo=s.get("reason", "Sugerido pelo FlowMaster")
                ) for s in sugestoes_raw
            ]
        )
    except Exception as e:
        print(f"Erro no SkillAgent: {e}")
        # Fallback gracioso em vez de erro 500
        return SkillSuggestionsResponse(sugestoes=[])