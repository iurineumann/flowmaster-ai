# backend/meeting_agent.py

import logging
from sqlalchemy.orm import Session
from .services.llm_service import LLMService
from .services.context_data_service import ContextDataService
from .utils.event_dispatcher import dispatch_event

logger = logging.getLogger(__name__)

class MeetingAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.context_service = ContextDataService(db)

    async def process(self, user_id: int) -> dict:
        """
        Analisa o contexto e sugere uma reunião se necessário.
        """
        logger.info(f"🤖 [MeetingAgent] Analisando necessidade de reunião para {user_id}...")

        try:
            user_context = await self.context_service.get_aggregated_context(user_id)
            
            prompt = """
            Analise o contexto de trabalho do usuário (tarefas, alertas).
            Determine se há um bloqueio ou tema crítico que exija uma reunião imediata (War Room, Daily Extra, Alinhamento).
            
            Retorne JSON:
            {
                "is_required": boolean,
                "title": "Título da Reunião",
                "duration_minutes": 30,
                "suggested_agenda": ["Item 1", "Item 2"],
                "context_source": "Motivo baseado nas tasks"
            }
            Se não for necessário, retorne is_required: false.
            """

            suggestion = await self.llm_service.generate_response(prompt, context=user_context)

            if "error" in suggestion:
                return self._get_fallback()

            if suggestion.get("is_required"):
                await dispatch_event({
                    "event_type": "MEETING_SUGGESTED",
                    "user_id": user_id,
                    "suggestion": suggestion
                })

            return suggestion

        except Exception as e:
            logger.error(f"[MeetingAgent] Erro: {e}")
            return self._get_fallback()

    def _get_fallback(self):
        return {
            "is_required": False,
            "title": "Nenhuma Reunião Necessária",
            "duration_minutes": 0,
            "suggested_agenda": [],
            "context_source": "Análise padrão"
        }