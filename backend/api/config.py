# backend/api/config.py (VERSÃO FINAL CORRIGIDA - Com PATCH para preferências)

import os
from fastapi import APIRouter, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from aiocache import cached
from cachetools import TTLCache # Para o cache in-memory do GET /user

# Importa as dependências e serviços
from ..db.database import get_db
from ..services.config_repository import ConfigRepository, populate_initial_data
from ..utils.security import get_current_user_id
from ..api.schemas import SystemModuleDetail, UserModulePreference, UserConfig
from cachetools.keys import hashkey


# --- Configuração de Cache para GET /modules (Redis) ---
CACHE_BACKEND = "aiocache.backends.redis.RedisCache"
CONFIG_CACHE_KWARGS = {
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 3600 # Cache de 1 hora no Redis
}

# --- Configuração de Cache para GET /user (In-Memory para a rota POST/PATCH) ---
# Usamos cachetools.TTLCache para a rota GET /user, pois facilita a invalidação manual
# após um PATCH, o que é crucial para as configurações do usuário.
CONFIG_CACHE = TTLCache(maxsize=10, ttl=3600) # Cache de 1 hora

def user_config_cache_key(user_id: int, db: Session):
    """Gera a chave de cache para a configuração do usuário."""
    # A chave do cache deve ser baseada apenas no user_id
    return user_id

router = APIRouter()

# Endpoint 1: Detalhes dos Módulos do Sistema
@router.get("/modules", response_model=List[SystemModuleDetail])
@cached(
    CACHE_BACKEND, 
    key_builder=lambda db: "system_modules_all", # Chave fixa para cache global
    **CONFIG_CACHE_KWARGS
)
async def get_system_modules(db: Session = Depends(get_db)):
    """
    Retorna a lista completa dos módulos do sistema disponíveis (Cached por 1h).
    """
    repo = ConfigRepository(db)
    
    # Garante a população inicial do DB (usado para SQLite/dev)
    if not repo.get_all_system_modules():
        populate_initial_data(db)

    db_modules = repo.get_all_system_modules()
    
    # Pydantic faz a conversão do modelo SQLAlchemy para o modelo de resposta
    return db_modules


# Endpoint 2: Configuração e Preferências do Usuário (GET)
# Usa cache in-memory do cachetools para facilitar a invalidação manual
@router.get("/user", response_model=UserConfig)
# Nota: O decorator cached do cachetools deve ser usado em funções SÍNCRONAS.
@cached(CONFIG_CACHE, key=user_config_cache_key) 
def get_user_config(
    user_id: int = Depends(get_current_user_id), # ID vem do JWT
    db: Session = Depends(get_db) # Injeta a sessão do DB
):
    """
    Retorna as preferências de dashboard de um usuário específico, usando o ID do JWT.
    """
    repo = ConfigRepository(db)
    
    # Garante que o registro base do usuário e as preferências padrão existam
    repo.ensure_user_config_exists(user_id=user_id) 

    # 1. Busca a configuração geral (theme)
    db_user_config = repo.get_user_config(user_id)
    
    # 2. Busca as preferências de módulo
    db_prefs = repo.get_user_module_preferences(user_id)
    
    # 3. Mapeia os dados do ORM para o Pydantic UserConfig
    module_preferences = [
        UserModulePreference(
            module_id=pref.module_id,
            is_active=pref.is_active,
            display_order=pref.display_order
        ) for pref in db_prefs
    ]

    return UserConfig(
        user_id=db_user_config.user_id,
        theme=db_user_config.theme,
        modules=module_preferences
    )


# Endpoint 3: Atualização das Preferências do Usuário (PATCH)
# ✅ MODIFICAÇÃO APLICADA: Uso do método PATCH
@router.patch("/user/preferences", response_model=UserConfig)
def update_user_module_preferences_endpoint(
    # Recebe uma lista do schema Pydantic, que o FastAPI traduz do JSON
    preferences: List[UserModulePreference], 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    """
    [PATCH] Atualiza a coleção de preferências dos módulos do usuário (ordem, status ativo/inativo).
    Usado pelo recurso drag-and-drop do frontend.
    """
    repo = ConfigRepository(db)
    
    # 1. Atualiza as preferências no repositório (DB)
    db_prefs = repo.update_user_module_preferences(user_id, preferences)
    
    # 2. Limpa o Cache de Configuração do Usuário
    # A chave do cache precisa ser limpa para que a próxima requisição GET /user traga os dados novos.
    cache_key = user_config_cache_key(user_id, db)
    if cache_key in CONFIG_CACHE:
        del CONFIG_CACHE[cache_key]
        print(f"🗑️ [Cache] Configuração do usuário {user_id} limpa.")

    # 3. Retorna a configuração completa atualizada
    # Busca a configuração geral (theme)
    db_user_config = repo.get_user_config(user_id)
    
    # Mapeia os dados do ORM atualizados para o Pydantic UserConfig
    module_preferences = [
        UserModulePreference(
            module_id=pref.module_id,
            is_active=pref.is_active,
            display_order=pref.display_order
        ) for pref in db_prefs
    ]

    return UserConfig(
        user_id=db_user_config.user_id,
        theme=db_user_config.theme,
        modules=module_preferences
    )