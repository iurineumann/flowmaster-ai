# backend/api/skill.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from aiocache import cached

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from ..skill_agent import SkillAgent

router = APIRouter()

class SkillItem(BaseModel):
    skill: str
    relevancia: str
    motivo: str
    # ✅ Novos campos para o Modal
    summary: Optional[str] = "Conteúdo recomendado para aprimoramento profissional."
    type: Optional[str] = "Recurso"
    tags: List[str] = []
    source: Optional[str] = "Web"
    link: Optional[str] = None

class SkillSuggestionsResponse(BaseModel):
    suggestions: List[SkillItem]

@router.get("/sugestoes", response_model=SkillSuggestionsResponse)
@cached(ttl=600)
async def get_skill_suggestions(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = SkillAgent(db)
        sugestoes_raw = await agent.analyze_user_context(user.id)
        
        normalized_items = []
        for s in sugestoes_raw:
            skill_name = s.get("skill") or s.get("name") or "Competência"
            
            # Fallback inteligente de Link
            raw_link = s.get("link") or s.get("url")
            if not raw_link or "example.com" in raw_link:
                safe_name = skill_name.replace(" ", "+")
                raw_link = f"https://www.google.com/search?q={safe_name}+tutorial"

            normalized_items.append(SkillItem(
                skill=skill_name,
                relevancia=s.get("relevancia") or s.get("relevance") or "Média",
                motivo=s.get("motivo") or s.get("reason") or "Relevante para o contexto atual",
                summary=s.get("summary") or s.get("description") or f"Aprenda sobre {skill_name} para melhorar seu desempenho.",
                type=s.get("type") or "Artigo",
                tags=s.get("tags") or [],
                source=s.get("source") or "Recomendação IA",
                link=raw_link
            ))

        response_obj = SkillSuggestionsResponse(suggestions=normalized_items)
        
        return response_obj.model_dump()

    except Exception as e:
        print(f"Erro no SkillAgent: {e}")
        return {"suggestions": []}