# backend/api/config.py

import os
from fastapi import APIRouter, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from aiocache import cached, Cache
from aiocache.backends.redis import RedisCache

from ..db.database import get_db
from ..services.config_repository import ConfigRepository, populate_initial_data
from ..utils.security import get_current_user_id
from ..api.schemas import SystemModuleDetail, UserModulePreference, UserConfig

# --- Configuração de Cache (Padronizado) ---
CACHE_KWARGS = {
    'cache': RedisCache,
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 3600
}

router = APIRouter()

def modules_cache_key(func, *args, **kwargs):
    return "system_modules_all"

def user_config_cache_key(func, *args, **kwargs):
    user_id = kwargs.get('user_id')
    return f"user_config:{user_id}"

# Endpoint 1: Detalhes dos Módulos do Sistema
@router.get("/modules", response_model=List[SystemModuleDetail])
@cached(
    key_builder=modules_cache_key,
    **CACHE_KWARGS
)
async def get_system_modules(db: Session = Depends(get_db)):
    repo = ConfigRepository(db)
    
    if not repo.get_all_system_modules():
        populate_initial_data(db)

    db_modules = repo.get_all_system_modules()
    
    # Convert SQLAlchemy ORM objects to pydantic-serializable dicts
    modules_serializable = [SystemModuleDetail.model_validate(m).model_dump() for m in db_modules]
    return modules_serializable

# Endpoint 2: Configuração e Preferências do Usuário (GET)
@router.get("/user", response_model=UserConfig)
@cached(
    key_builder=user_config_cache_key,
    **CACHE_KWARGS
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
        user_config = UserConfig(
            user_id=db_user_config.user_id,
            theme=db_user_config.theme,
            modules=module_preferences
        )
        return user_config.model_dump()
    
    user_config = UserConfig(user_id=user_id, theme="dark", modules=module_preferences)
    return user_config.model_dump()

# Endpoint 3: Atualizar Preferências do Usuário (PATCH)
@router.patch("/user/modules", response_model=UserConfig)
async def update_user_module_preferences_endpoint(
    preferences: List[UserModulePreference], 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    repo = ConfigRepository(db)
    
    db_prefs = repo.update_user_module_preferences(user_id, preferences)
    
    try:
        # Usa os mesmos kwargs, mas instancia o Cache para invalidar
        cache = Cache(RedisCache, endpoint=os.environ.get('REDIS_ENDPOINT', "redis"), port=6379)
        cache_key = f"user_config:{user_id}"
        await cache.delete(cache_key)
        print(f"🗑️ [Cache] Configuração do usuário {user_id} invalidada (Redis).")
    except Exception as e:
        print(f"⚠️ [Cache] Falha ao invalidar cache do usuário {user_id}: {e}")

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