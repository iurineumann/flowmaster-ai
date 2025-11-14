# backend/db/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON 
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
    # Username pode ser o email ou um nome de usuário interno
    username = Column(String, unique=True, index=True, nullable=False) 
    
    # NOVOS CAMPOS: Vínculo com Microsoft
    email = Column(String, unique=True, index=True, nullable=True) # Email real
    microsoft_id = Column(String, unique=True, index=True, nullable=True) # OID da Microsoft (Imutável)
    
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True) 
    is_active = Column(Boolean, default=True)
    
    # Relações
    user_config = relationship("UserConfigModel", back_populates="user", uselist=False)
    preferences = relationship("UserModulePreferenceModel", back_populates="user")

# ----------------------------------------------------------------------
# 2. Modelos de Configuração (Para Agente de Configuração)
# Referenciado em: config_repository.py
# ----------------------------------------------------------------------

class SystemModuleDetailModel(Base):
    """Modelo de banco de dados para os Módulos de IA disponíveis (global)."""
    __tablename__ = "system_modules"

    id = Column(String, primary_key=True, index=True) 
    name = Column(String, index=True)
    description = Column(String)
    api_endpoint = Column(String) 
    grid_column_span = Column(Integer)
    
    user_preferences = relationship("UserModulePreferenceModel", back_populates="module_detail")

class UserConfigModel(Base):
    """Configuração geral do usuário (ex: tema)."""
    __tablename__ = "user_configs"
    
    # Correção: Adiciona ForeignKey para vincular 'user_configs' à tabela 'users'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, index=True) 
    theme = Column(String, default="dark") 
    
    # Relacionamento de volta
    user = relationship("UserModel", back_populates="user_config") 

class UserModulePreferenceModel(Base):
    """Preferências do usuário para cada módulo (ativo/ordem de exibição)."""
    __tablename__ = "user_module_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True) # Vinculo com User
    module_id = Column(String, ForeignKey("system_modules.id"), index=True) # Vinculo com Modulo
    
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=99)
    
    user = relationship("UserModel", back_populates="preferences")
    module_detail = relationship("SystemModuleDetailModel", back_populates="user_preferences")

# ----------------------------------------------------------------------
# 3. Modelo de Políticas (Para o PCC Agent)
# Referenciado em: policy_service.py
# ----------------------------------------------------------------------
class PolicyModel(Base):
    """Modelo de banco de dados para Políticas de Conformidade (Compliance)."""
    __tablename__ = "policies"
    
    id = Column(String, primary_key=True, index=True) 
    name = Column(String)
    description = Column(String)
    
    policy_rule = Column(JSON) 
    
    applies_to = Column(String, index=True) 
    is_active = Column(Boolean, default=True)