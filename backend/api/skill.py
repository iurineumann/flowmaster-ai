# backend/api/skill.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from ..skill_agent import SkillAgent
# Se estiver usando aiocache direto, garanta que o retorno seja dict
from aiocache import cached

router = APIRouter()

class SkillItem(BaseModel):
    skill: str
    relevancia: str
    motivo: str

class SkillSuggestionsResponse(BaseModel):
    sugestoes: List[SkillItem]

@router.get("/sugestoes", response_model=SkillSuggestionsResponse)
@cached(ttl=600) # Cache simples
async def get_skill_suggestions(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = SkillAgent(db)
        sugestoes_raw = await agent.analyze_user_context(user.id)
        
        response_obj = SkillSuggestionsResponse(
            sugestoes=[
                SkillItem(
                    skill=s.get("name", "Skill"),
                    relevancia=s.get("relevance", "Média"),
                    motivo=s.get("reason", "Sugerido pelo FlowMaster")
                ) for s in sugestoes_raw
            ]
        )
        
        # ✅ CORREÇÃO CRÍTICA: .model_dump() converte Pydantic -> Dict
        # Isso permite que o @cached serialize para JSON sem erro.
        return response_obj.model_dump()

    except Exception as e:
        print(f"Erro no SkillAgent: {e}")
        # Retorna dict vazio válido
        return {"sugestoes": []}