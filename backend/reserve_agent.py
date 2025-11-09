# backend/reserve_agent.py
from pydantic import BaseModel
from typing import Optional

# Importa o conector LLM real para análise
from backend.llm_connector import llm_connector, RawContextItem

class ReserveSuggestionModel(BaseModel):
    # Modelo Pydantic para o retorno (alinhado com a interface do Frontend)
    resource_id: str
    resource_type: str # 'desk' | 'meeting_room' | 'quiet_pod'
    suggested_location: str
    reason: str

class ReserveAgent:
    """
    Agente responsável por sugerir a melhor posição de trabalho (reserva inteligente) 
    baseado no foco, na agenda e no mapa de reservas.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        
    def get_suggestion(self, current_focus_tag: str) -> Optional[ReserveSuggestionModel]:
        
        # 1. Simula a entrada de dados (Agenda/Status)
        calendar_mock = "Próxima reunião 'Alinhamento Cliente X' em 2 horas."
        status_mock = "Online, focado no BUG CRÍTICO (necessita de deep work)."
        
        # 2. Chamada ao LLM para Decisão (Otimização do Espaço)
        prompt = (
            f"O usuário ({self.user_id}) está em status '{status_mock}' com foco em '{current_focus_tag}'. "
            f"Seus compromissos são: '{calendar_mock}'. Qual recurso de trabalho (quiet_pod, desk, meeting_room) "
            f"e localização seria mais otimizado para o foco no bug crítico? Justifique."
        )

        # llm_response = llm_connector.analyze_and_summarize_context(
        #     items=[RawContextItem(subject_or_title=current_focus_tag, content_preview=prompt)],
        #     user_name=f"Usuário ID {self.user_id}"
        # )

        # MOCK DE DECISÃO: Sugere um Quiet Pod para concentração máxima
        if "BUG CRÍTICO" in current_focus_tag.upper():
            return ReserveSuggestionModel(
                resource_id="POD-E2",
                resource_type="quiet_pod",
                suggested_location="3º Andar, Zona Engenharia (silenciosa)",
                reason="O foco crítico exige concentração máxima para a depuração. O Quiet Pod POD-E2 é ideal para 'deep work' e próximo à equipe."
            )
        
        return None