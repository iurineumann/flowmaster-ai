# backend/utils/event_dispatcher.py

import logging
import os
import json
from aio_pika import connect_robust, Message, DeliveryMode

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "flowmaster_events"

async def dispatch_event(event: any):
    """
    Envia evento para RabbitMQ. Aceita Dict ou Pydantic.
    """
    try:
        if isinstance(event, dict):
            event_type = event.get("event_type", "UNKNOWN")
            payload = event
        else:
            event_type = getattr(event, "event_type", "UNKNOWN")
            payload = event.model_dump() if hasattr(event, "model_dump") else event.dict()

        if "event_type" not in payload:
            payload["event_type"] = str(event_type)

        connection = await connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(QUEUE_NAME, durable=True)
            
            await channel.default_exchange.publish(
                Message(
                    body=json.dumps(payload).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT
                ),
                routing_key=QUEUE_NAME,
            )
        
        logger.info(f"🐰 Evento enviado: {event_type}")
        
    except Exception as e:
        logger.error(f"❌ Falha no RabbitMQ: {e}")