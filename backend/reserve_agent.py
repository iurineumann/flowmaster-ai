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
        Analisa o contexto do usuário e sugere uma reserva de recurso real via LLM.
        """
        logger.info(f"🤖 [ReserveAgent] Iniciando análise para usuário {user_id}...")

        try:
            # 1. Busca Contexto Real (Tarefas, Calendário, etc.)
            # Note: ContextDataService já deve lidar internamente com a falta de tokens
            user_context = await self.context_service.get_aggregated_context(user_id)
            
            # 2. Pergunta à LLM
            prompt = """
            Com base nas tarefas e reuniões atuais do usuário, determine se ele precisa reservar um recurso físico (Sala, Cabine, Equipamento).
            
            Regras:
            - Reuniões confidenciais -> Sala de Reunião
            - Programação pareada -> Estação Dupla
            - Trabalho profundo/complexo -> Cabine de Foco
            
            Retorne JSON:
            {
                "is_suggested": boolean,
                "resource_name": "Nome do Recurso",
                "time_slot": "Horário sugerido",
                "reason": "Justificativa curta"
            }
            """

            suggestion = await self.llm_service.generate_response(prompt, context=user_context)

            # 3. Validação
            if "error" in suggestion:
                logger.warning("[ReserveAgent] Falha na LLM, retornando vazio.")
                return {
                    "is_suggested": False,
                    "resource_name": None,
                    "reason": "Análise indisponível"
                }

            # 4. Dispara Evento se sugerido
            if suggestion.get("is_suggested"):
                await dispatch_event({
                    "event_type": "RESERVATION_SUGGESTED",
                    "user_id": user_id,
                    "suggestion": suggestion
                })

            return suggestion

        except Exception as e:
            logger.error(f"[ReserveAgent] Erro fatal: {e}")
            return {
                "is_suggested": False,
                "resource_name": None,
                "reason": "Erro interno no agente"
            }