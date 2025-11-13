# backend/api/config.py (VERSÃO FINAL CORRIGIDA - Sem Circular Import)

from fastapi import APIRouter, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from cachetools import cached, TTLCache 

# NOVO: Importa os modelos Pydantic do novo arquivo de schemas
from .schemas import SystemModuleDetail, UserModulePreference, UserConfig 

# Importa as dependências e serviços
from ..db.database import get_db # Dependência da Sessão
from ..services.config_repository import ConfigRepository, populate_initial_data
from ..utils.security import get_current_user_id # Dependência de JWT

router = APIRouter()

# --- Configuração de Cache (Mantida) ---
CONFIG_CACHE = TTLCache(maxsize=10, ttl=3600) # Cache de 1 hora

def user_config_cache_key(user_id: int, db: Session):
    # A chave do cache deve ser baseada apenas no user_id, pois os outros params não variam
    return user_id

# Endpoint 1: Detalhes dos Módulos do Sistema
@router.get("/modules", response_model=List[SystemModuleDetail])
@cached(CONFIG_CACHE, key=lambda db: "system_modules_all") # Cache global
def get_system_modules(db: Session = Depends(get_db)):
    """
    Retorna a lista completa dos módulos do sistema disponíveis.
    """
    repo = ConfigRepository(db)
    
    # Garante a população inicial do DB (usado para SQLite/dev)
    if not repo.get_all_system_modules():
        populate_initial_data(db)

    db_modules = repo.get_all_system_modules()
    
    # Pydantic faz a conversão do modelo SQLAlchemy para o modelo de resposta
    return db_modules


# Endpoint 2: Configuração e Preferências do Usuário
@router.get("/user", response_model=UserConfig)
@cached(CONFIG_CACHE, key=user_config_cache_key)
def get_user_config(
    user_id: int = Depends(get_current_user_id), # ID vem do JWT
    db: Session = Depends(get_db) # Injeta a sessão do DB
):
    """
    Retorna as preferências de dashboard de um usuário específico, usando o ID do JWT.
    Rota: /config/user (não mais /config/user/{user_id})
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