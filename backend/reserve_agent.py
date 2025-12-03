# backend/reserve_agent.py

import logging
from sqlalchemy.orm import Session
from .services.llm_service import LLMService
from .services.context_data_service import ContextDataService
from .utils.event_dispatcher import dispatch_event
from .utils.data_security import security_service

logger = logging.getLogger(__name__)

class ReserveAgent:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.context_service = ContextDataService(db)

    async def process(self, user_id: int) -> dict:
        """
        Analisa a necessidade de recursos físicos baseada na agenda e tarefas.
        """
        try:
            # 1. Busca Contexto Rico
            user_context = await self.context_service.get_aggregated_context(user_id)
            
            # Sanitiza contexto para log (segurança)
            logger.info(f"🤖 [ReserveAgent] Analisando contexto para usuário {user_id}")
            
            # 2. Prompt de Engenharia
            prompt = """
            Você é um gestor de facilities AI.
            Analise o contexto do usuário (cargo, reuniões, tarefas).
            Determine se ele precisa reservar um recurso físico AGORA.
            
            Critérios:
            - Reunião "Confidencial" ou "Client" -> Sala de Reunião
            - Tarefa "Deep Work" ou "Análise" -> Cabine de Foco
            - Reunião "Pair Programming" -> Estação Dupla
            
            Retorne JSON:
            {
                "is_suggested": boolean,
                "resource_name": "Nome do Recurso (ex: Sala B2)",
                "time_slot": "Sugestão de horário (ex: 14:00)",
                "reason": "Justificativa clara e curta"
            }
            """

            # 3. Chamada LLM
            suggestion = await self.llm_service.generate_response(prompt, context=user_context)

            # 4. Validação e Despacho
            if "error" in suggestion:
                return self._fallback_response()

            if suggestion.get("is_suggested"):
                # Sanitiza antes de despachar evento
                safe_payload = security_service.sanitize_log_payload(suggestion)
                
                await dispatch_event({
                    "event_type": "RESERVATION_SUGGESTED",
                    "user_id": user_id,
                    "suggestion": safe_payload
                })

            return suggestion

        except Exception as e:
            logger.error(f"❌ [ReserveAgent] Erro: {e}")
            return self._fallback_response()

    def _fallback_response(self):
        return {
            "is_suggested": False,
            "resource_name": None,
            "reason": "Análise automática indisponível."
        }