# backend/db/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base # Importa a Base declarativa de database.py

# ----------------------------------------------------------------------
# 1. Modelo de Usuário (Para Autenticação)
# Referenciado em: security.py, config_repository.py
# ----------------------------------------------------------------------
class UserModel(Base):
    """Modelo de banco de dados para a tabela de Usuários."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False) # Email ou login
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True) # Nome completo
    is_active = Column(Boolean, default=True)
    
    # Relações: Permite acessar configurações e preferências diretamente do objeto User
    config = relationship("UserConfigModel", back_populates="user", uselist=False)
    preferences = relationship("UserModulePreferenceModel", back_populates="user")

# ----------------------------------------------------------------------
# 2. Modelos de Configuração (Para Agente de Configuração)
# Referenciado em: config_repository.py
# ----------------------------------------------------------------------

class SystemModuleDetailModel(Base):
    """Modelo de banco de dados para os Módulos de IA disponíveis (global)."""
    __tablename__ = "system_module_details"

    # O 'id' aqui é a chave de string (ex: 'context_agent')
    id = Column(String, primary_key=True, index=True) 
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    api_endpoint = Column(String, nullable=False)
    grid_column_span = Column(Integer, default=1)
    
class UserConfigModel(Base):
    """Configuração geral do usuário (ex: tema, idioma)."""
    __tablename__ = "user_config"
    
    # ID da configuração é o mesmo que o user_id (relação one-to-one)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    theme = Column(String, default="dark") # Ex: 'light' ou 'dark'
    
    user = relationship("UserModel", back_populates="config")

class UserModulePreferenceModel(Base):
    """Preferências do usuário para cada módulo (ativo/ordem de exibição)."""
    __tablename__ = "user_module_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    module_id = Column(String, ForeignKey("system_module_details.id"), index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=99)
    
    user = relationship("UserModel", back_populates="preferences")
    # module = relationship("SystemModuleDetailModel") # Opcional: relação de volta para o módulo

# ----------------------------------------------------------------------
# 3. Modelo de Políticas (Para o PCC Agent)
# Referenciado em: policy_service.py
# ----------------------------------------------------------------------
class PolicyModel(Base):
    """Modelo de banco de dados para Políticas de Conformidade (Compliance)."""
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    # A política se aplica a 'global' ou a um 'module_id' (ex: 'llm_agent')
    applies_to = Column(String, index=True, default="global") 
    # Regra em formato JSON (ex: {"action": "mask", "target_data": "cpf"})
    policy_rule = Column(JSON, nullable=True) 
    # Outros campos de auditoria (ex: created_at, updated_at) seriam adicionados aqui