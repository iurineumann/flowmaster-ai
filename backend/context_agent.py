# backend/context_agent.py

import logging
from sqlalchemy.orm import Session
from typing import Dict, Any
from .services.llm_service import LLMService
from .services.context_data_service import ContextDataService

logger = logging.getLogger(__name__)

class ContextAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.context_service = ContextDataService(db)

    async def analyze_user_focus(self, user_id: int) -> Dict[str, Any]:
        """
        Analisa as tarefas e reuniões do usuário para determinar o foco principal e alertas.
        """
        try:
            # 1. Coleta de Dados Reais (ADO + Perfil)
            raw_context = await self.context_service.get_aggregated_context(user_id)
            
            # Se não houver tarefas, retorna estado padrão
            if not raw_context.get("active_tasks"):
                return self._get_default_state()

            # 2. Prompt de Análise de Contexto
            prompt = """
            Você é um Agile Coach AI. Analise a lista de tarefas do usuário (Azure DevOps).
            
            DADOS:
            {context_data}
            
            TAREFA:
            1. Identifique o "Foco Atual" (Um resumo de 3-5 palavras do que ele está construindo agora).
            2. Identifique a "Sprint/Meta" (O objetivo geral das tarefas).
            3. Gere "Alertas" se houver tarefas com status 'Blocked', 'Bug' ou 'Critical'.
            
            Retorne JSON estrito:
            {{
                "current_focus": "ex: Refatoração do Módulo de Auth",
                "current_sprint": "ex: Sprint Estabilidade",
                "alerts": ["Alerta 1", "Alerta 2"]
            }}
            """
            
            # Formata o prompt com os dados (limitado para não estourar tokens)
            formatted_prompt = prompt.format(context_data=str(raw_context)[:2000])

            # 3. Chamada à LLM
            analysis = await self.llm_service.generate_response(formatted_prompt, json_mode=True)
            
            if "error" in analysis:
                logger.warning("[ContextAgent] Falha na análise LLM, usando heurística básica.")
                return self._heuristic_fallback(raw_context)

            return {
                "focus": analysis.get("current_focus", "Desenvolvimento Geral"),
                "sprint": analysis.get("current_sprint", "Sprint Atual"),
                "alerts": analysis.get("alerts", [])
            }

        except Exception as e:
            logger.error(f"[ContextAgent] Erro crítico: {e}")
            return self._get_default_state()

    def _heuristic_fallback(self, context: Dict) -> Dict:
        """Fallback se a LLM falhar: pega o projeto da primeira task."""
        tasks = context.get("active_tasks", [])
        if not tasks:
            return self._get_default_state()
            
        project = tasks[0].get("project", "Projeto Principal")
        return {
            "focus": f"Atuando em {project}",
            "sprint": "Backlog",
            "alerts": []
        }

    def _get_default_state(self) -> Dict:
        return {
            "focus": "Sem foco definido",
            "sprint": "Planejamento",
            "alerts": ["Conecte o ADO para ver análises"]
        }