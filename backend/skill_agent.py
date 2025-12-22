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
        Gera sugestões de skills com priorização baseada em tarefas críticas.
        """
        try:
            # 1. Busca dados reais (ADO + Perfil)
            context = await self.context_service.get_aggregated_context(user_id)
            
            # ✅ Prompt de Engenharia Avançado (Priorização + Estrutura Rica)
            prompt = """
            Você é um Mentor Técnico Sênior. Analise as tarefas do usuário (Azure DevOps).
            
            REGRAS DE PRIORIZAÇÃO:
            1. ALTA PRIORIDADE: Identifique tarefas com status 'Blocked', 'Bug', 'Critical' ou atrasadas. Sugira skills para resolver esses bloqueios IMEDIATAMENTE.
            2. MÉDIA PRIORIDADE: Tecnologias centrais do projeto atual.
            3. BAIXA PRIORIDADE: Soft skills ou tendências futuras.
            
            Para cada sugestão, forneça detalhes ricos para um modal de aprendizado.
            Se tiver acesso a ferramentas de busca, encontre links reais.
            
            Retorne JSON estrito:
            {
                "suggestions": [
                    {
                        "skill": "Nome do Recurso",
                        "relevancia": "Alta" | "Média" | "Baixa",
                        "motivo": "Por que isso resolve a tarefa X (seja específico)",
                        "summary": "Resumo de 2 linhas sobre o conteúdo.",
                        "type": "Curso" | "Documentação" | "Vídeo" | "Ferramenta",
                        "tags": ["Tag1", "Tag2"],
                        "source": "Udemy" | "Microsoft Learn" | "YouTube" | "Oficial",
                        "link": "https://url-real-ou-vazia"
                    }
                ]
            }
            """

            response = await self.llm_service.generate_response(prompt, context=context)
            
            # Normalização da resposta
            if "suggestions" in response:
                return response["suggestions"]
            if "sugestoes" in response:
                return response["sugestoes"]
            
            return []

        except Exception as e:
            logger.error(f"[SkillAgent] Erro: {e}")
            return []