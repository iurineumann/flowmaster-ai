# backend/reserve_mock.py
from pydantic import BaseModel
from typing import List, Dict

# Estrutura de dados para a Sugestão de Reserva
class ReserveSuggestion(BaseModel):
    """Modelo para uma sugestão de reserva de mesa/recurso."""
    resource_id: str
    resource_type: str # 'desk', 'meeting_room', 'quiet_pod'
    suggested_location: str # e.g., 'Mesa A12'
    reason: str # Por que a IA sugeriu este local?

# MOCK DA BASE DE DADOS DE RECURSOS E EXPERTISE (Simulando um 'Digital Twin' do Escritório)
RESERVE_MOCK_DATABASE: Dict[str, ReserveSuggestion] = {
    # Regra 1: Próximo à especialista em Segurança/IAM (Elena)
    "SECURITY_IAM": ReserveSuggestion(
        resource_id="A12",
        resource_type="desk",
        suggested_location="Mesa A12 (Próxima à Dra. Elena Santos)",
        reason="O foco atual exige expertise em Segurança e IAM. Sentar próximo à especialista chave facilita o acesso rápido."
    ),
    # Regra 2: Próximo ao time de QA/Testes (Thiago)
    "QA_TESTING": ReserveSuggestion(
        resource_id="C05",
        resource_type="desk",
        suggested_location="Mesa C05 (Próxima à equipe de QA)",
        reason="O projeto exige revisão e alinhamento de testes de UI/UX com o QA Sênior, Thiago Almeida."
    ),
    # Regra 3: Reuniões longas e foco profundo
    "MEETING_DEEP_FOCUS": ReserveSuggestion(
        resource_id="POD_2",
        resource_type="quiet_pod",
        suggested_location="Quiet Pod #2 (Sala de Foco Silencioso)",
        reason="A IA detectou uma reunião longa no seu cronograma. Sugestão para focar sem interrupções."
    )
}

# Mapeamento do Foco (Project Tag) para a Regra de Reserva
FOCUS_TO_RESERVE_MOCK: Dict[str, str] = {
    "CLIENTE_X": "SECURITY_IAM", # Problema de Pagamento/Segurança
    "PROJETO_Y": "QA_TESTING",   # Problema de Testes de UI
}