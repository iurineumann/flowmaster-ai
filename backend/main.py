# backend/main.py (VERSÃO FINAL DE PRODUÇÃO COM CORS E CONFIGURAÇÃO)

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # NOVO: Para Comunicação Frontend

# Importa todos os roteadores
from backend.api import context
from backend.api import skill 
from backend.api import reserve 
from backend.api import config 
from backend.api import notifications 
from backend.api import meeting
from backend.api import chat
from backend.api import auth
from backend.api import admin

# Importa a função de criação de DB e a Configuração do DB para ser inicializada
from backend.db.database import create_db_and_tables

# Importa a função de criação de DB e a Configuração do DB para ser inicializada
# REMOVIDO: A chamada para create_db_and_tables() foi removida daqui para EVITAR a race condition 
# do Gunicorn. Ela será executada separadamente no docker-compose.yml.
# from backend.db.database import create_db_and_tables

# --- Variáveis de Configuração de Produção (PONTO 6) ---

# CORS: Lista de URLs do frontend permitidas (separadas por vírgula)
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", 
    "" # Deixa vazio, confiando no .env para desenvolvimento
).split(",")

# JWT/Segurança: Chave Secreta para Assinatura de Tokens.
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", 
    "" # Deixa vazio, confiando no .env para desenvolvimento
)

# --- Inicialização ---

# 1. Inicialização do FastAPI
app = FastAPI(title="FlowMaster AI Backend Core", version="0.1.0")

# --- MIDDLEWARE: CORS (Obrigatório para Frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, 
    allow_credentials=True,        
    allow_methods=["*"],           
    allow_headers=["*"],           
)
# ----------------------------------------------------


# 1. Rota raiz (Status)
@app.get("/")
def read_root():
    """Endpoint de teste para verificar se o backend está ativo."""
    return {"app_name": "FlowMaster AI", 
            "status": "online", 
            "environment": os.environ.get("ENV", "development")}

# 2. Inclusão dos Roteadores
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"]) # NOVO: Rota de Login
app.include_router(config.router, prefix="/config", tags=["Configuração do Sistema"])
app.include_router(context.router, prefix="/contexto", tags=["Contexto e Produtividade"])
app.include_router(skill.router, prefix="/skill", tags=["Desenvolvimento e Aprendizado"])
app.include_router(reserve.router, prefix="/reserva", tags=["Produtividade e Agendamento"])
app.include_router(meeting.router, prefix="/meeting", tags=["Otimização de Reuniões"])
app.include_router(notifications.router, prefix="/notifications", tags=["Comunicação"])
app.include_router(chat.router, prefix="/chat", tags=["Chat e Geração"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])