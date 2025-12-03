# backend/utils/multi_layer_cache.py

import json
import logging
import os
from functools import wraps
from typing import Callable, Any
import redis.asyncio as redis

# Configuração de Logger
logger = logging.getLogger(__name__)

# Configuração do Redis (lê do docker-compose)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Cliente Global
redis_client = None

async def get_redis():
    """Garante uma instância única do cliente Redis."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

def cache_decorator(key_prefix: str, ttl: int = 60):
    """
    Decorator de cache utilizando Redis.
    Armazena o resultado da função serializado em JSON.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # 1. Conectar ao Redis
                client = await get_redis()
                
                # 2. Gerar Chave Única
                # Simplificação: usa apenas o prefixo e o ID do usuário se for o primeiro argumento
                # Em produção, recomenda-se hashing completo dos argumentos.
                cache_key = f"{key_prefix}"
                if args:
                    # Tenta usar o ID do usuário se for um objeto UserModel ou ID direto
                    user_arg = args[0]
                    if hasattr(user_arg, 'id'):
                        cache_key += f":{user_arg.id}"
                    else:
                        cache_key += f":{str(user_arg)}"

                # 3. Tentar Ler do Cache
                cached_data = await client.get(cache_key)
                if cached_data:
                    logger.info(f"✅ Cache HIT: {cache_key}")
                    return json.loads(cached_data)
                
                # 4. Executar Função Real (Cache Miss)
                logger.info(f"⚠️ Cache MISS: {cache_key}")
                result = await func(*args, **kwargs)
                
                # 5. Salvar no Cache
                # O resultado DEVE ser um dicionário (dict) ou lista, não objeto Pydantic
                # Os endpoints (context.py, skill.py) já foram corrigidos para usar .model_dump()
                if result is not None:
                    await client.setex(
                        name=cache_key,
                        time=ttl,
                        value=json.dumps(result)
                    )
                
                return result

            except Exception as e:
                # Fallback: Se o Redis falhar, executa a função sem cache e loga o erro
                # Isso impede que a aplicação pare se o Redis cair.
                logger.error(f"❌ Erro no Cache Redis: {e}")
                return await func(*args, **kwargs)
                
        return wrapper
    return decorator