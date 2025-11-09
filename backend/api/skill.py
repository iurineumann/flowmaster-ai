# backend/api/skill.py
from fastapi import APIRouter
from typing import List
from ..skill_agent import SkillAgent, SkillSuggestionModel 

router = APIRouter()

@router.get("/suggestions/{project_tag}", response_model=List[SkillSuggestionModel])
def get_skill_suggestions(project_tag: str):
    """
    Endpoint que usa o Agente Skill-Boost para sugerir cursos ou especialistas.
    """
    # Hardcoded user_id para PoC
    user_id = 42 
    
    skill_agent = SkillAgent(user_id=user_id)
    suggestions = skill_agent.get_suggestions(current_focus_tag=project_tag)
    
    return suggestions