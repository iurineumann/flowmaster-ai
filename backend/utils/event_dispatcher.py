# backend/utils/event_dispatcher.py

from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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

def dispatch_event(event: any):
    """
    Simula o envio de um evento para um barramento (ex: RabbitMQ/Kafka).
    Aceita tanto Dicionários quanto Modelos Pydantic.
    """
    try:
        # Verifica se é dict ou objeto para acessar o tipo
        if isinstance(event, dict):
            event_type = event.get("event_type", "UNKNOWN")
            payload = event
        else:
            event_type = getattr(event, "event_type", "UNKNOWN")
            payload = event.dict() if hasattr(event, "dict") else str(event)

        print(f"📣 EVENT DISPATCHED: {str(event_type).upper()}")
        logger.info(f"Event payload: {payload}")
        
    except Exception as e:
        logger.error(f"Falha ao despachar evento: {e}")