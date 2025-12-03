# backend/skill_agent.py

import logging
from sqlalchemy.orm import Session
from typing import List, Dict
from .services.llm_service import LLMService
from .services.context_data_service import ContextDataService

logger = logging.getLogger(__name__)

class SkillAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.context_service = ContextDataService(db)

    async def analyze_user_context(self, user_id: int) -> List[Dict]:
        """
        Gera sugestões de skills baseadas nas tasks do ADO e perfil.
        """
        # 1. Contexto
        context = await self.context_service.get_aggregated_context(user_id)
        
        # 2. Prompt
        prompt = """
        Analise as tarefas pendentes e o projeto atual do usuário.
        Sugira 3 competências técnicas (Skills) ou ferramentas que ajudariam a completar essas tarefas.
        
        Retorne um JSON com uma chave "suggestions" contendo uma lista de objetos:
        [{ "name": "Nome da Skill", "relevance": "Alta/Média", "reason": "Por que é útil" }]
        """

        # 3. LLM
        response = await self.llm_service.generate_response(prompt, context=context)
        
        # 4. Tratamento
        if "suggestions" in response:
            return response["suggestions"]
        
        return []