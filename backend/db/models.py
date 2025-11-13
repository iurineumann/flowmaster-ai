# backend/db/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON 
from sqlalchemy.orm import relationship
from ..db.database import Base

# --- 1. Módulos do Sistema (Globais) ---
class SystemModuleDetailModel(Base):
    """Detalhes de um módulo do sistema (global)."""
    __tablename__ = "system_modules"
    
    # Chave primária: Usaremos o ID string (ex: 'context_agent')
    id = Column(String, primary_key=True, index=True) 
    name = Column(String, index=True)
    description = Column(String)
    api_endpoint = Column(String) 
    grid_column_span = Column(Integer)
    
    # Relacionamento: Um módulo pode ter muitas preferências de usuário
    user_preferences = relationship("UserModulePreferenceModel", back_populates="module_detail")

# --- 2. Preferências de Módulos por Usuário ---
class UserModulePreferenceModel(Base):
    """Mapeamento de preferência de módulo por usuário."""
    __tablename__ = "user_module_preferences"
    
    id = Column(Integer, primary_key=True, index=True) 
    user_id = Column(Integer, index=True) # ID do Usuário (Chave de busca principal)
    
    # Chave estrangeira para SystemModuleDetailModel
    module_id = Column(String, ForeignKey("system_modules.id"), index=True) 
    
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=99)
    
    # Relacionamento de volta para o módulo (detalhes)
    module_detail = relationship("SystemModuleDetailModel", back_populates="user_preferences")

# --- 3. Configuração Geral do Usuário (Ex: Tema) ---
class UserConfigModel(Base):
    """Configuração geral do usuário (Tema, etc.)."""
    __tablename__ = "user_configs"
    
    # ❌ CORREÇÃO: Adiciona a Chave Estrangeira 'users.id'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, index=True) 
    theme = Column(String, default="dark") # Ex: 'light', 'dark'
    
    # ✅ NOVO: Relacionamento de volta para o modelo 'UserModel'
    user = relationship("UserModel", back_populates="user_config") 

# --- 4. Policy Model ---
class PolicyModel(Base):
    """Modelo para armazenar políticas de compliance, mascaramento e segurança."""
    __tablename__ = "policies"
    
    id = Column(String, primary_key=True, index=True) # Ex: 'global_masking_policy', 'lgpd_compliance_rule'
    name = Column(String)
    description = Column(String)
    
    # Regra em formato JSON: Define o que mascarar, quais regras aplicar.
    # Ex: {"action": "mask", "target_data": ["cpf", "email"], "regex": "..."}
    policy_rule = Column(JSON) 
    
    # Aplicação: 'global' ou 'module_id' (foreign key)
    applies_to = Column(String, index=True) 
    is_active = Column(Boolean, default=True)

# --- 5. Modelo de Usuário (Para Autenticação Real) ---
class UserModel(Base):
    """Modelo para armazenar usuários e suas credenciais hasheadas."""
    __tablename__ = "users"
    
    # user_id é a chave que usamos no JWT
    id = Column(Integer, primary_key=True, index=True) 
    
    # Campo para o login (email ou nome de usuário)
    username = Column(String, unique=True, index=True) 
    
    # Senha hasheada com bcrypt
    hashed_password = Column(String) 
    
    is_active = Column(Boolean, default=True)
    
    # Opcional: Relacionamento de volta para a Configuração (1-para-1)
    user_config = relationship("UserConfigModel", back_populates="user")