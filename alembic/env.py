# alembic/env.py
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy.pool import NullPool
from alembic import context

# Carrega o .env para que o Alembic possa ver o DATABASE_URL
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Adiciona o diretório 'backend' ao sys.path para encontrar os modelos
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importa a Base dos seus modelos
from backend.db.models import Base
# Importa todos os seus modelos para que a 'Base' os conheça
from backend.db import models 

# Configuração do Alembic (lê alembic.ini)
config = context.config

# Interpreta o arquivo de configuração para logging do Python.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Configuração Central ---
# Define o 'target_metadata' para o Alembic (autogenerate)
target_metadata = Base.metadata

def get_url():
    """Retorna a URL do banco de dados a partir do .env."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL não está configurado no .env")
    # Corrige URL do psycopg2 (se necessário)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def run_migrations_offline() -> None:
    """Roda migrações em modo 'offline'."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Roda migrações em modo 'online' (conectado ao DB)."""
    
    # Cria a configuração do engine
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()}, # Usa a URL do .env
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True, # Compara tipos de colunas
            compare_server_default=True # Compara defaults
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()