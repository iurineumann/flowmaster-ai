# backend/db/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON 
from sqlalchemy.orm import relationship
from .database import Base 

# ----------------------------------------------------------------------
# 1. Modelo de Usuário (Para Autenticação)
# ----------------------------------------------------------------------
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False) 
    
    email = Column(String, unique=True, index=True, nullable=True)
    microsoft_id = Column(String, unique=True, index=True, nullable=True) # OID
    
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True) 
    is_active = Column(Boolean, default=True)
    
    # Relações
    user_config = relationship("UserConfigModel", back_populates="user", uselist=False)
    preferences = relationship("UserModulePreferenceModel", back_populates="user")
    ado_connections = relationship("UserAdoConnection", back_populates="user") # Relação com Conexões ADO

# ----------------------------------------------------------------------
# 2. Modelos de Configuração (Para Agente de Configuração)
# ----------------------------------------------------------------------

class SystemModuleDetailModel(Base):
    __tablename__ = "system_modules"

    id = Column(String, primary_key=True, index=True) 
    name = Column(String, index=True)
    description = Column(String)
    api_endpoint = Column(String) 
    grid_column_span = Column(Integer)
    
    user_preferences = relationship("UserModulePreferenceModel", back_populates="module_detail")

class UserConfigModel(Base):
    __tablename__ = "user_configs"
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, index=True) 
    theme = Column(String, default="dark") 
    
    user = relationship("UserModel", back_populates="user_config") 

class UserModulePreferenceModel(Base):
    __tablename__ = "user_module_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    module_id = Column(String, ForeignKey("system_modules.id"), index=True)
    
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=99)
    
    user = relationship("UserModel", back_populates="preferences")
    module_detail = relationship("SystemModuleDetailModel", back_populates="user_preferences")

# ----------------------------------------------------------------------
# 3. Modelo de Políticas (Para o PCC Agent)
# ----------------------------------------------------------------------
class PolicyModel(Base):
    __tablename__ = "policies"
    
    id = Column(String, primary_key=True, index=True) 
    name = Column(String)
    description = Column(String)
    policy_rule = Column(JSON) 
    applies_to = Column(String, index=True) 
    is_active = Column(Boolean, default=True)

# ----------------------------------------------------------------------
# 4. NOVOS MODELOS: Configuração Dinâmica do Azure DevOps (ADO)
# ----------------------------------------------------------------------
class UserAdoConnection(Base):
    """Armazena as conexões ADO (Organizações) que um usuário configurou."""
    __tablename__ = "user_ado_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_url = Column(String, nullable=False) # Ex: https://dev.azure.com/MinhaOrg
    is_active = Column(Boolean, default=True)
    
    user = relationship("UserModel", back_populates="ado_connections")
    projects = relationship("AdoProjectConfig", back_populates="connection", cascade="all, delete-orphan")
    
    # Garante que um usuário não possa adicionar a mesma Org duas vezes
    __table_args__ = (UniqueConstraint('user_id', 'organization_url', name='_user_org_uc'),)

class AdoProjectConfig(Base):
    """Armazena os projetos específicos que o usuário deseja monitorar."""
    __tablename__ = "ado_project_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("user_ado_connections.id"), nullable=False)
    project_name = Column(String, nullable=False) # O nome do Projeto no ADO
    is_active = Column(Boolean, default=True)
    
    connection = relationship("UserAdoConnection", back_populates="projects")