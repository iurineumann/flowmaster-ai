# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configuração da URL de Conexão com o PostgreSQL
# Os valores são os mesmos definidos no docker-compose.yml
SQLALCHEMY_DATABASE_URL = "postgresql://flowmaster_user:flowmaster_password@flowmaster-ai-postgres:5432/flowmaster_db"

# O 'flowmaster-ai-postgres' é o nome do serviço Docker, que é resolvido internamente.
# O engine é responsável pela comunicação com o DB
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal será a sessão do banco de dados (o objeto usado para CRUD)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para todos os modelos de DB (ORM)
Base = declarative_base()

# Função para criar uma sessão de DB por requisição (dependência do FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()