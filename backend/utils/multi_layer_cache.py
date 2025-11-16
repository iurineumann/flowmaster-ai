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
REDIS_ENDPOINT = os.environ.get('REDIS_ENDPOINT', "redis")
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

_redis_client: Optional[Redis] = None
_memory_cache_instance: Optional['MemoryCache'] = None

# --- Nomes das Chaves de Estatísticas no Redis ---
STATS_CACHE_HITS_L1 = "stats:cache:hits_l1" # Hits Memória
STATS_CACHE_HITS_L2 = "stats:cache:hits_l2" # Hits Redis
STATS_CACHE_MISSES = "stats:cache:misses"   # Misses (Chamadas reais)
STATS_LLM_CALLS = "stats:llm_calls"         # Contador de chamadas de LLM/Função

# --- Cache Classes ---

class MemoryCache:
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()

    async def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    return value
                else:
                    del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        expiry = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expiry)

class RedisCache:
    def __init__(self, redis_client: Optional[Redis]):
        self._redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        try:
            data = await self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        if not self._redis:
            return
        try:
            data = pickle.dumps(value)
            await self._redis.setex(key, ttl, data)
        except Exception:
            pass

# --- Initialization/Accessor Functions ---

def get_memory_cache() -> 'MemoryCache':
    global _memory_cache_instance
    if _memory_cache_instance is None:
        _memory_cache_instance = MemoryCache()
    return _memory_cache_instance

async def get_redis_client() -> Optional[Redis]:
    global _redis_client
    if _redis_client is not None:
        # Tenta um ping rápido para verificar a saúde antes de retornar
        try:
            await _redis_client.ping()
            return _redis_client
        except Exception:
            print("⚠️ [Cache] Conexão Redis perdida. Tentando reconectar...")
            _redis_client = None # Força a reconexão
            
    try:
        _redis_client = redis.Redis(
            host=REDIS_ENDPOINT, 
            port=REDIS_PORT, 
            decode_responses=False
        )
        await _redis_client.ping()
        print(f"✅ [Cache] Conexão Redis estabelecida com {REDIS_ENDPOINT}:{REDIS_PORT}.")
    except Exception as e:
        print(f"❌ [Cache] Falha ao conectar ao Redis: {e}. O cache L2 estará desativado.")
        _redis_client = None
            
    return _redis_client

async def get_redis_cache() -> 'RedisCache':
    client = await get_redis_client()
    return RedisCache(client)

# --- Decorator Core (COM RASTREAMENTO DE STATS) ---

def multi_layer_cache(
    ttl: int = 3600,
    memory_ttl: int = 600,
    key_builder: Optional[Callable] = None,
    skip_cache_func: Callable = lambda result: result is None,
    track_llm_call: bool = False # Flag para rastrear chamadas de LLM
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            
            memory_cache = get_memory_cache()
            redis_client = await get_redis_client() # Cliente real para stats
            
            def default_key_builder(*a, **kw) -> str:
                arg_repr = str((a, tuple(sorted(kw.items()))))
                return f"{func.__module__}.{func.__name__}:{arg_repr}"

            builder = key_builder or default_key_builder
            key = builder(*args, **kwargs)

            # 1. Memory Cache Lookup (Layer 1)
            val = await memory_cache.get(key)
            if val is not None:
                if redis_client:
                    await redis_client.incr(STATS_CACHE_HITS_L1)
                return val

            # 2. Redis Cache Lookup (Layer 2)
            redis_cache = RedisCache(redis_client) # Wrapper para get/set
            val = None 
            if redis_cache._redis: 
                try:
                    val = await redis_cache.get(key)
                    if val is not None:
                        await redis_client.incr(STATS_CACHE_HITS_L2)
                        await memory_cache.set(key, val, ttl=memory_ttl)
                        return val
                except Exception as e:
                    print(f"⚠️ [Cache] Redis GET falhou: {e}")
                    pass 

            # 3. Cache Miss: Chamar a função real
            if redis_client:
                await redis_client.incr(STATS_CACHE_MISSES)
                # Se esta flag for True, rastreia como uma chamada de LLM (custo)
                if track_llm_call:
                    await redis_client.incr(STATS_LLM_CALLS)
            
            val = await func(*args, **kwargs)
            
            # 4. Cache the result
            if not skip_cache_func(val):
                if redis_cache._redis: 
                    try:
                        await redis_cache.set(key, val, ttl=ttl)
                    except Exception as e:
                        print(f"⚠️ [Cache] Redis SET falhou: {e}")
                        pass
                
                await memory_cache.set(key, val, ttl=memory_ttl)
                
            return val
        return wrapper
    return decorator

# --- NOVA FUNÇÃO DE ESTATÍSTICAS ---

async def get_cache_stats() -> Dict[str, int]:
    """
    Busca as estatísticas de cache e LLM diretamente do Redis.
    """
    stats = {
        "hits_l1": 0,
        "hits_l2": 0,
        "misses": 0,
        "llm_calls": 0
    }
    
    client = await get_redis_client()
    if not client:
        print("⚠️ [Stats] Não foi possível conectar ao Redis para buscar estatísticas.")
        return stats # Retorna zero se o Redis estiver offline

    try:
        keys = [STATS_CACHE_HITS_L1, STATS_CACHE_HITS_L2, STATS_CACHE_MISSES, STATS_LLM_CALLS]
        values = await client.mget(keys)
        
        stats["hits_l1"] = int(values[0] or 0)
        stats["hits_l2"] = int(values[1] or 0)
        stats["misses"] = int(values[2] or 0)
        stats["llm_calls"] = int(values[3] or 0)
        
    except Exception as e:
        print(f"❌ [Stats] Erro ao buscar estatísticas do Redis: {e}")
    
    return stats