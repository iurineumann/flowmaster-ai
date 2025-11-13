# backend/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


# --- Configuração do Banco de Dados ---

# Padrão: Usa uma variável de ambiente. Se não for definida, usa SQLite local.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./flowmaster_config.db" # SQLite local para desenvolvimento
)

# --- CORREÇÃO DE ERRO: Define connect_args condicionalmente ---
# 'check_same_thread' é obrigatório para SQLite, mas inválido para PostgreSQL.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Para PostgreSQL, o argumento é ignorado ou deve ser um dicionário vazio.
    connect_args = {}

# Cria o Engine (conexão)
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args, # Usa a variável condicional
    pool_pre_ping=True # Recomendado para robustez em ambientes com pool de conexão (PostgreSQL)
)

# Cria a SessionLocal para injeção de dependência
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos declarativos
Base = declarative_base()

# --- Dependência de Sessão (Para injeção no FastAPI) ---

def get_db():
    """
    Função geradora para fornecer uma sessão de banco de dados por requisição.
    Garante que a sessão seja fechada após o uso (try...finally).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Funções de Inicialização ---

def create_db_and_tables():
    """
    Cria as tabelas no banco de dados e as popula com dados iniciais
    (se elas ainda não existirem).
    """
    # Importa os modelos para que o SQLAlchemy os reconheça
    from . import models
    Base.metadata.create_all(bind=engine)
    
    print("💡 [DB] Tabelas criadas com sucesso.")