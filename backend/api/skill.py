# backend/api/skill.py
from fastapi import APIRouter
from typing import List
from backend.skill_mock import SKILL_MOCK_DATABASE, SkillSuggestion

router = APIRouter()

@router.get("/suggestions/{project_tag}", response_model=List[SkillSuggestion])
def get_skill_boost_suggestions(project_tag: str):
    """
    Simula o endpoint Skill-Boost que fornece sugestões de cursos/especialistas 
    baseadas no tag do projeto (contexto).
    """
    # Garante que a tag seja em maiúsculas para o mock
    tag_upper = project_tag.upper()
    
    # Busca sugestões no mock
    suggestions = SKILL_MOCK_DATABASE.get(tag_upper, [])
    
    if not suggestions:
        return [
            SkillSuggestion(
                type="info",
                title="Nenhuma Sugestão Encontrada",
                context_reason="O FlowMaster AI está calibrando o Skill-Boost para este projeto."
            )
        ]
        
    return suggestions