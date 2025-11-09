# backend/api/skill.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from cachetools import cached, TTLCache

# --- Modelos Pydantic para a Resposta da API (Tipagem Explicita) ---
# Usamos a mesma estrutura definida em frontend/src/types.ts

# Cache de 60 segundos
AGENT_DATA_CACHE = TTLCache(maxsize=128, ttl=60) 

def agent_cache_key(user_id: int) -> int:
    return user_id

class SkillSuggestion(BaseModel):
    """Modelo para uma sugestão de skill individual."""
    title: str
    score: int # Percentual de relevância
    link: Optional[str] = None # URL opcional para um curso/recurso

class SkillAgentData(BaseModel):
    """Modelo da resposta principal do Agente Skill."""
    suggestions: List[SkillSuggestion]

# --- Roteador FastAPI ---

router = APIRouter()

@router.get("/sugestoes/{user_id}", response_model=SkillAgentData)
@cached(AGENT_DATA_CACHE, key=agent_cache_key)
def get_skill_suggestions(user_id: int):
    """
    Endpoint que simula a análise do contexto do usuário (ex: um bug crítico) 
    e sugere habilidades de desenvolvimento e aprendizado relevantes.
    """
    
    # 📝 Simulação da Lógica de IA: 
    # Contexto Base: O foco atual é um BUG CRÍTICO de 'Falha de Pagamento' 
    # envolvendo 'criptografia' (baseado em graph_mock.py).
    
    suggestions = [
        SkillSuggestion(
            title="Criptografia em Python (Nível Avançado)",
            score=92,
            link="https://lms.flowmaster.ai/crypto-advanced"
        ),
        SkillSuggestion(
            title="Design Patterns e Refatoração de Código",
            score=85,
            link="https://lms.flowmaster.ai/refactoring-patterns"
        ),
        SkillSuggestion(
            title="Comunicação em Crises Técnicas",
            score=70,
            link=None # Opcional: link pode ser nulo se for um workshop interno
        ),
        SkillSuggestion(
            title="Introdução ao PySpark (Análise Big Data)",
            score=35, # Score baixo por ser menos relevante para a crise atual
            link=None
        )
    ]

    return SkillAgentData(suggestions=suggestions)