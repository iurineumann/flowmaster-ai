# backend/config_service.py (FINAL - LÓGICA DE CRUD COM POSTGRESQL)
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

# Importa os modelos de banco de dados (ORM) e Pydantic
from .db_models import DBModuleConfig, DBUserConfig, DBUserModulePreference
# Os modelos Pydantic são mantidos aqui como contratos de API
class UserModulePreference(BaseModel):
    module_id: str
    is_active: bool = True
    display_order: int
    consent_given: bool = True

class UserConfig(BaseModel):
    user_id: int
    modules: List[UserModulePreference]
    theme: str = "dark"

class ModuleConfig(BaseModel):
    id: str
    name: str
    is_available: bool
    description: str
    llm_model_name: str
    llm_prompt_template: str
    api_endpoint: str
    display_order: int
    api_key_system: Optional[str] = None # Retornará None, pois a chave não está no modelo DB por segurança

# --- Funções de Ajuda (Mapeamento Pydantic <-> DB) ---

def _map_db_user_to_pydantic(db_user: DBUserConfig) -> UserConfig:
    """Converte o objeto DBUserConfig (com relacionamentos) para Pydantic."""
    
    # Mapeia as preferências de módulo relacionadas
    pydantic_modules = [
        UserModulePreference(
            module_id=p.module_id,
            is_active=p.is_active,
            display_order=p.display_order,
            consent_given=p.consent_given
        )
        for p in db_user.modules
    ]

    return UserConfig(
        user_id=db_user.user_id,
        theme=db_user.theme,
        modules=pydantic_modules
    )

# --- Lógica de CRUD do Serviço (Usando Sessão do DB) ---

# -------------------------- SISTEMA (ModuleConfig) --------------------------

def get_system_modules(db: Session) -> List[ModuleConfig]:
    """READ: Retorna a lista de módulos disponíveis no sistema (do DB)."""
    
    stmt = select(DBModuleConfig).order_by(DBModuleConfig.display_order)
    db_modules = db.scalars(stmt).all()
    
    return [
        ModuleConfig.from_orm(m)
        for m in db_modules
    ]

# -------------------------- USUÁRIO (UserConfig) --------------------------

def get_user_configuration(db: Session, user_id: int) -> Optional[UserConfig]:
    """READ: Retorna a configuração de um usuário existente, ou None."""
    
    # Carrega o usuário e suas preferências em uma única query
    stmt = select(DBUserConfig).filter(DBUserConfig.user_id == user_id)
    db_user = db.scalar(stmt)
    
    if db_user is None:
        return None
        
    return _map_db_user_to_pydantic(db_user)

def create_user_configuration(db: Session, user_config: UserConfig) -> UserConfig:
    """CREATE: Cria uma nova configuração de usuário."""
    
    # 1. Cria o objeto principal
    db_user = DBUserConfig(
        user_id=user_config.user_id,
        theme=user_config.theme
    )
    
    # 2. Adiciona as preferências de módulo relacionadas
    for pref in user_config.modules:
        db_pref = DBUserModulePreference(
            module_id=pref.module_id,
            is_active=pref.is_active,
            display_order=pref.display_order,
            consent_given=pref.consent_given,
            user_id=user_config.user_id # Garante a FK
        )
        db_user.modules.append(db_pref)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return _map_db_user_to_pydantic(db_user)

def update_user_configuration(db: Session, user_id: int, config_update: UserConfig) -> Optional[UserConfig]:
    """UPDATE: Atualiza (PUT/PATCH) uma configuração de usuário existente."""
    
    db_user = db.scalar(select(DBUserConfig).filter(DBUserConfig.user_id == user_id))
    
    if db_user is None:
        return None

    # 1. Atualiza campos simples
    db_user.theme = config_update.theme
    
    # 2. Atualiza relacionamentos (Deleta os antigos e insere os novos)
    # A configuração do SQLAlchemy (cascade="all, delete-orphan") facilita a exclusão
    
    # Limpa a lista de módulos (o delete-orphan remove do DB)
    db_user.modules.clear()
    
    # Adiciona os novos módulos
    for pref in config_update.modules:
        db_pref = DBUserModulePreference(
            module_id=pref.module_id,
            is_active=pref.is_active,
            display_order=pref.display_order,
            consent_given=pref.consent_given,
            user_id=user_id
        )
        db_user.modules.append(db_pref)

    db.commit()
    db.refresh(db_user)
    
    return _map_db_user_to_pydantic(db_user)

def delete_user_configuration(db: Session, user_id: int) -> bool:
    """DELETE: Remove uma configuração de usuário."""
    
    # A exclusão do DBUserConfig irá, via CASCADE, excluir as preferências de módulo
    stmt = delete(DBUserConfig).where(DBUserConfig.user_id == user_id)
    result = db.execute(stmt)
    db.commit()
    
    return result.rowcount > 0 # Retorna True se uma linha foi afetada