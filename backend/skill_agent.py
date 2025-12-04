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
        Gera sugestões de skills.
        """
        try:
            context = await self.context_service.get_aggregated_context(user_id)
            
            # ✅ Prompt Otimizado para Web Search
            prompt = """
            Analise as tarefas e o projeto atual do usuário.
            Sugira 3 competências técnicas (Hard/Soft Skills) essenciais.
            
            IMPORTANTE:
            - Se tiver acesso a ferramentas de busca (Web Search), USE-AS para encontrar a URL oficial da documentação ou um curso real de alta qualidade.
            - Se não encontrar, deixe o link vazio.
            
            Retorne APENAS o JSON final no seguinte formato:
            {
                "suggestions": [
                    { 
                        "skill": "Nome da Skill", 
                        "relevancia": "Alta", 
                        "motivo": "Explicação curta",
                        "link": "https://link-real-encontrado..." 
                    }
                ]
            }
            """

            response = await self.llm_service.generate_response(prompt, context=context)
            
            # Normalização
            if "suggestions" in response:
                return response["suggestions"]
            if "sugestoes" in response:
                return response["sugestoes"]
            
            return []

        except Exception as e:
            logger.error(f"[SkillAgent] Erro: {e}")
            return []