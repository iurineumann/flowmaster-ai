# backend/utils/multi_layer_cache.py

import asyncio
import functools
import os
import pickle
import threading
import time
from typing import Any, Optional, Dict, Callable
import redis.asyncio as redis
from redis.asyncio import Redis

# --- Globals and Configuration ---

# Configuração para conexão com o Redis. Usa o nome do serviço 'redis' no Docker Compose.
REDIS_ENDPOINT = os.environ.get('REDIS_ENDPOINT', "redis")
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Global Redis client e Memory Cache (por processo Uvicorn/Gunicorn)
_redis_client: Optional[Redis] = None
_memory_cache_instance: Optional['MemoryCache'] = None

# --- Cache Classes ---

class MemoryCache:
    """Cache em memória (process-local) com suporte a TTL e thread-safe."""

    def __init__(self):
        # {key: (value, expiry_timestamp)}
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()

    async def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    return value
                else:
                    # Expira
                    del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        expiry = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expiry)


class RedisCache:
    """Wrapper para o cache Redis assíncrono (redis.asyncio)."""

    def __init__(self, redis_client: Optional[Redis]):
        # O cliente pode ser None se a conexão falhar, permitindo o fallback.
        self._redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        try:
            # Pega o dado binário
            data = await self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            # Falha de conexão/deserialização (silenciosa)
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        if not self._redis:
            return
        try:
            # Serializa o objeto
            data = pickle.dumps(value)
            await self._redis.setex(key, ttl, data)
        except Exception as e:
            # Falha de conexão/serialização (silenciosa)
            pass

# --- Initialization/Accessor Functions ---

def get_memory_cache() -> 'MemoryCache':
    """Retorna a instância do cache em memória (local ao processo)."""
    global _memory_cache_instance
    if _memory_cache_instance is None:
        _memory_cache_instance = MemoryCache()
    return _memory_cache_instance

async def get_redis_client() -> Optional[Redis]:
    """Retorna o cliente Redis assíncrono, inicializando e testando a conexão se necessário."""
    global _redis_client
    # Se já estiver inicializado, retorna
    if _redis_client is not None:
        return _redis_client
        
    try:
        # Tenta a conexão
        _redis_client = redis.Redis(
            host=REDIS_ENDPOINT, 
            port=REDIS_PORT, 
            decode_responses=False # Crucial para pickle.dumps/loads
        )
        # Verifica a conexão
        await _redis_client.ping()
        print(f"✅ [Cache] Conexão Redis estabelecida com {REDIS_ENDPOINT}:{REDIS_PORT}.")
    except Exception as e:
        # Falha na conexão, seta para None.
        print(f"❌ [Cache] Falha ao conectar ao Redis em {REDIS_ENDPOINT}:{REDIS_PORT}. Operando em modo de cache de memória local apenas. Erro: {e}")
        _redis_client = None
            
    return _redis_client

async def get_redis_cache() -> 'RedisCache':
    """Retorna a instância do wrapper RedisCache, contendo o cliente (ou None)."""
    client = await get_redis_client()
    return RedisCache(client)

# --- Decorator Core ---

def multi_layer_cache(
    ttl: int = 3600,
    memory_ttl: int = 600,
    key_builder: Optional[Callable] = None,
    skip_cache_func: Callable = lambda result: result is None
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            
            memory_cache = get_memory_cache()
            
            # --- Key Builder ---
            def default_key_builder(*a, **kw) -> str:
                # Usa o caminho da função e os argumentos.
                arg_repr = str((a, tuple(sorted(kw.items()))))
                return f"{func.__module__}.{func.__name__}:{arg_repr}"

            builder = key_builder or default_key_builder
            key = builder(*args, **kwargs)
            # -------------------

            # 1. Memory Cache Lookup (Layer 1)
            val = await memory_cache.get(key)
            if val is not None:
                return val

            # 2. Redis Cache Lookup (Layer 2)
            redis_cache = await get_redis_cache()
            val = None 
            if redis_cache._redis: 
                try:
                    val = await redis_cache.get(key)
                    if val is not None:
                        # Promove para o cache em memória para a próxima chamada
                        await memory_cache.set(key, val, ttl=memory_ttl)
                        return val
                except Exception as e:
                    print(f"⚠️ [Cache] Redis GET falhou. Prosseguindo para a função. Erro: {e}")
                    pass 

            # 3. Call the function
            val = await func(*args, **kwargs)
            
            # 4. Cache the result
            if not skip_cache_func(val):
                # Escreve no Redis (L2)
                if redis_cache._redis: 
                    try:
                        await redis_cache.set(key, val, ttl=ttl)
                    except Exception as e:
                        print(f"⚠️ [Cache] Redis SET falhou. Erro: {e}")
                        pass
                
                # Escreve na Memória (L1)
                await memory_cache.set(key, val, ttl=memory_ttl)
                
            return val
        return wrapper
    return decorator