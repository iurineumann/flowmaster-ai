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
        Gera sugestões de skills baseadas nas tasks reais do usuário.
        """
        try:
            context = await self.context_service.get_aggregated_context(user_id)
            
            prompt = """
            Analise as tarefas e o projeto atual do usuário.
            Sugira 3 competências técnicas (Hard/Soft Skills) que aumentariam sua produtividade agora.
            
            Retorne JSON:
            {
                "suggestions": [
                    { "name": "Nome da Skill", "relevance": "Alta/Média", "reason": "Motivo breve" }
                ]
            }
            """

            response = await self.llm_service.generate_response(prompt, context=context)
            
            if "suggestions" in response:
                return response["suggestions"]
            
            return []

        except Exception as e:
            logger.error(f"[SkillAgent] Erro: {e}")
            return []