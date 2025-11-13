# backend/utils/event_dispatcher.py

from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

# --- Definição dos Eventos do Sistema ---

class BaseSystemEvent(BaseModel):
    """Modelo base para todos os eventos do FlowMaster AI."""
    timestamp: str = datetime.now().isoformat()
    event_type: str
    payload: Dict[str, Any]

class CriticalContextDetectedEvent(BaseSystemEvent):
    """Evento disparado quando a IA detecta um foco de trabalho crítico."""
    event_type: str = "critical_context_detected"
    
class SkillGapIdentifiedEvent(BaseSystemEvent):
    """Evento disparado após a sugestão de Skill ser gerada."""
    event_type: str = "skill_gap_identified"

# --- Dispatcher de Eventos ---

def dispatch_event(event: BaseSystemEvent):
    """
    Simula o envio de um evento para um Message Broker (Kafka, RabbitMQ, etc.)
    ou para um sistema de logs/auditoria.
    """
    print("------------------------------------------------------------------")
    print(f"📣 EVENT DISPATCHED: {event.event_type.upper()}")
    print(f"  Payload: {event.payload}")
    print(f"  Time: {event.timestamp}")
    print("------------------------------------------------------------------")

    # Em produção: O código real de envio para o broker estaria aqui.
    pass