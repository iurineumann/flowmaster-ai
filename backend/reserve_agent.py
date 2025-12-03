# backend/reserve_agent.py

import logging
from sqlalchemy.orm import Session
from .services.llm_service import LLMService
from .services.context_data_service import ContextDataService
from .utils.event_dispatcher import dispatch_event

logger = logging.getLogger(__name__)

class ReserveAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.context_service = ContextDataService(db)

    async def process(self, user_id: int) -> dict:
        """
        Analisa o contexto do usuário e sugere uma reserva de recurso.
        """
        logger.info(f"🤖 [ReserveAgent] Iniciando análise para usuário {user_id}...")

        # 1. Busca Contexto Real (Tarefas, Calendário, etc.)
        user_context = await self.context_service.get_aggregated_context(user_id)
        
        # 2. Pergunta à LLM
        prompt = """
        Com base nas tarefas e reuniões atuais do usuário, sugira uma reserva de recurso físico necessária.
        Exemplos: 'Sala de Reunião' se tiver muitas reuniões, 'Estação de Trabalho Dupla' se tiver pair programming, 'Cabine de Foco' se tiver tarefas complexas.
        
        Retorne um JSON com:
        - is_suggested: boolean
        - resource_name: string (ex: Sala B2)
        - time_slot: string (ex: 14:00 - 15:00)
        - reason: string (breve justificativa)
        """

        suggestion = await self.llm_service.generate_response(prompt, context=user_context)

        # 3. Validação e Fallback
        if "error" in suggestion:
            logger.warning("[ReserveAgent] Falha na LLM, usando fallback.")
            return {
                "is_suggested": False,
                "reason": "Não foi possível analisar sua agenda no momento."
            }

        # 4. Dispara Evento (RabbitMQ) se houver sugestão
        if suggestion.get("is_suggested"):
            await dispatch_event({
                "event_type": "RESERVATION_SUGGESTED",
                "user_id": user_id,
                "suggestion": suggestion
            })

        return suggestion