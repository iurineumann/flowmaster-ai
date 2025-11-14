# backend/api/config.py

import os
from fastapi import APIRouter, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from aiocache import cached, Cache

from ..db.database import get_db
from ..services.config_repository import ConfigRepository, populate_initial_data
from ..utils.security import get_current_user_id
from ..api.schemas import SystemModuleDetail, UserModulePreference, UserConfig

# --- Configuração de Cache (Padronizado) ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
CONFIG_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 3600 # Cache de 1 hora
}

router = APIRouter()

def user_config_cache_key(user_id: int, db: Session):
    return f"user_config:{user_id}"

# Endpoint 1: Detalhes dos Módulos do Sistema
@router.get("/modules", response_model=List[SystemModuleDetail])
@cached(
    CACHE_BACKEND, 
    key_builder=lambda db: "system_modules_all",
    **CONFIG_CACHE_KWARGS
)
async def get_system_modules(db: Session = Depends(get_db)):
    repo = ConfigRepository(db)
    
    # Esta é uma operação síncrona de DB, mas o FastAPI a executa em um threadpool
    if not repo.get_all_system_modules():
        populate_initial_data(db)

    db_modules = repo.get_all_system_modules()
    
    return db_modules

# Endpoint 2: Configuração e Preferências do Usuário (GET)
@router.get("/user", response_model=UserConfig)
@cached(
    CACHE_BACKEND, 
    key_builder=user_config_cache_key,
    **CONFIG_CACHE_KWARGS
)
async def get_user_config(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    repo = ConfigRepository(db)
    
    repo.ensure_user_config_exists(user_id=user_id) 

    db_user_config = repo.get_user_config(user_id)
    db_prefs = repo.get_user_module_preferences(user_id)
    
    module_preferences = [
        UserModulePreference(
            module_id=pref.module_id,
            is_active=pref.is_active,
            display_order=pref.display_order
        )
        for pref in db_prefs
    ]
    
    if db_user_config:
        return UserConfig(
            user_id=db_user_config.user_id,
            theme=db_user_config.theme,
            modules=module_preferences
        )
    
    return UserConfig(user_id=user_id, theme="dark", modules=module_preferences)

# Endpoint 3: Atualizar Preferências do Usuário (PATCH)
@router.patch("/user/modules", response_model=UserConfig)
async def update_user_module_preferences_endpoint(
    preferences: List[UserModulePreference], 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    repo = ConfigRepository(db)
    
    # 1. Atualiza o DB
    db_prefs = repo.update_user_module_preferences(user_id, preferences)
    
    # 2. Invalida o Cache (Assíncrono)
    try:
        cache = Cache(CACHE_BACKEND, **CONFIG_CACHE_KWARGS)
        cache_key = user_config_cache_key(user_id, db)
        await cache.delete(cache_key)
        print(f"🗑️ [Cache] Configuração do usuário {user_id} invalidada (Redis).")
    except Exception as e:
        print(f"⚠️ [Cache] Falha ao invalidar cache do usuário {user_id}: {e}")

    # 3. Retorna a configuração completa atualizada
    db_user_config = repo.get_user_config(user_id)
    
    module_preferences = [
        UserModulePreference(
            module_id=pref.module_id,
            is_active=pref.is_active,
            display_order=pref.display_order
        ) for pref in db_prefs
    ]
    
    return UserConfig(
        user_id=user_id,
        theme=db_user_config.theme,
        modules=module_preferences
    )