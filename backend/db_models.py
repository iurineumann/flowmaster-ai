# backend/db_models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.sqltypes import ARRAY
from .database import Base

# --- Mapeamento para Tabelas (ORM) ---

# 1. Tabela de Preferências de Módulos por Usuário (RELACIONAMENTO)
class DBUserModulePreference(Base):
    __tablename__ = "user_module_preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_id: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Chave estrangeira para a tabela de usuários
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_configs.user_id"))

# 2. Tabela de Configurações de Usuário (UserConfig)
class DBUserConfig(Base):
    __tablename__ = "user_configs"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    theme: Mapped[str] = mapped_column(String, default="dark")
    
    # Relacionamento: Um usuário tem muitas preferências de módulos
    modules = relationship("DBUserModulePreference", backref="owner", cascade="all, delete-orphan")
    
# 3. Tabela de Configurações de Módulos (ModuleConfig - Dados globais)
# Nota: Esta tabela é simplificada, no futuro usará JSONB para prompts/configs complexas
class DBModuleConfig(Base):
    __tablename__ = "system_modules_config"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(String)
    llm_model_name: Mapped[str] = mapped_column(String)
    llm_prompt_template: Mapped[str] = mapped_column(String)
    api_endpoint: Mapped[str] = mapped_column(String)
    display_order: Mapped[int] = mapped_column(Integer)
    # api_key_system será carregado de forma segura (Vault/Env Vars), não aqui.