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

# ✅ Modelo rico para suportar o Modal e Links
class SkillItem(BaseModel):
    skill: str
    relevancia: str
    motivo: str
    summary: Optional[str] = "Conteúdo recomendado para seu desenvolvimento."
    type: Optional[str] = "Recurso"
    tags: List[str] = []
    source: Optional[str] = "IA"
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
            # Garante que o nome da skill exista
            skill_name = s.get("skill") or s.get("name") or "Competência"
            
            # Fallback de Link: Se a IA não trouxer, cria busca no Google
            raw_link = s.get("link") or s.get("url")
            if not raw_link:
                safe_name = skill_name.replace(" ", "+")
                raw_link = f"https://www.google.com/search?q={safe_name}+documentation"

            normalized_items.append(SkillItem(
                skill=skill_name,
                relevancia=s.get("relevancia") or s.get("relevance") or "Média",
                motivo=s.get("motivo") or s.get("reason") or "Relevante para o projeto",
                summary=s.get("summary") or s.get("description") or f"Aprenda {skill_name} para desbloquear suas tarefas.",
                type=s.get("type") or "Artigo",
                tags=s.get("tags") or [],
                source=s.get("source") or "Web",
                link=raw_link
            ))

        return {"suggestions": normalized_items}

    except Exception as e:
        print(f"Erro no SkillAgent: {e}")
        return {"suggestions": []}