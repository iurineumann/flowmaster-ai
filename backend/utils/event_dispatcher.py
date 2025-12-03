# backend/utils/event_dispatcher.py

import logging
import os
import json
import asyncio
from aio_pika import connect_robust, Message, DeliveryMode

logger = logging.getLogger(__name__)

# Configuração do RabbitMQ
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "flowmaster_events"

async def dispatch_event(event: any):
    """
    Envia um evento para a fila do RabbitMQ.
    Aceita Dicionários ou Modelos Pydantic.
    """
    connection = None
    try:
        # 1. Normalização dos Dados (Dict ou Pydantic)
        if isinstance(event, dict):
            event_type = event.get("event_type", "UNKNOWN")
            payload = event
        else:
            event_type = getattr(event, "event_type", "UNKNOWN")
            # Converte Pydantic para dict
            payload = event.model_dump() if hasattr(event, "model_dump") else event.dict()

        # Adiciona metadados se não existirem
        if "event_type" not in payload:
            payload["event_type"] = str(event_type)

        message_body = json.dumps(payload).encode()

        # 2. Conexão e Publicação (RabbitMQ)
        # 'connect_robust' reconecta automaticamente se a conexão cair
        connection = await connect_robust(RABBITMQ_URL)
        
        async with connection:
            channel = await connection.channel()
            
            # Declara a fila (garante que ela existe)
            # durable=True: a fila sobrevive ao reinício do broker
            await channel.declare_queue(QUEUE_NAME, durable=True)
            
            # Publica a mensagem
            await channel.default_exchange.publish(
                Message(
                    body=message_body,
                    delivery_mode=DeliveryMode.PERSISTENT # Mensagem salva em disco
                ),
                routing_key=QUEUE_NAME,
            )

        print(f"🐰 EVENTO ENVIADO AO RABBITMQ: {event_type}")
        logger.info(f"Payload: {payload}")
        
    except Exception as e:
        logger.error(f"❌ Falha ao despachar evento para RabbitMQ: {e}")
        # Opcional: Implementar lógica de 'Dead Letter Queue' ou salvar em banco para retry