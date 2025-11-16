# backend/main.py (VERSÃO FINAL CORRIGIDA)

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa todos os roteadores
from backend.api import context
from backend.api import skill 
from backend.api import reserve 
from backend.api import config 
from backend.api import notifications 
from backend.api import meeting
from backend.api import chat
from backend.api import auth # Rota de Autenticação
from backend.api import admin # Rota de Admin

# --- Variáveis de Configuração ---

# CORS: Lista de URLs do frontend permitidas (separadas por vírgula)
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", 
    "http://localhost:5173,http://localhost:3000" # Padrão mínimo de dev
).split(",")

print(f"✅ [CORS] Configurado para permitir origens: {ALLOWED_ORIGINS}")

# --- Inicialização do FastAPI ---
app = FastAPI(title="FlowMaster AI Backend Core", version="0.1.0")

# --- MIDDLEWARE: CORS (Obrigatório para Frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, # Lista de origens permitidas
    allow_credentials=True,        # Permite cookies/tokens
    allow_methods=["*"],           # Permite todos os métodos (GET, POST, PATCH, etc.)
    allow_headers=["*"],           # Permite todos os headers (incluindo Authorization)
)

# --- Rota raiz (Status) ---
@app.get("/")
def read_root():
    return {"app_name": "FlowMaster AI", 
            "status": "online", 
            "environment": os.environ.get("ENV", "development")}

# --- Inclusão dos Roteadores (Com prefixo /api/v1) ---
PREFIX = "/api/v1" 

app.include_router(auth.router, prefix=f"{PREFIX}/auth", tags=["Autenticação"])
app.include_router(config.router, prefix=f"{PREFIX}/config", tags=["Configuração do Sistema"])
app.include_router(admin.router, prefix=f"{PREFIX}/admin", tags=["Administração"])
app.include_router(context.router, prefix=f"{PREFIX}/contexto", tags=["Agente: Contexto e Produtividade"])
app.include_router(skill.router, prefix=f"{PREFIX}/skill", tags=["Agente: Desenvolvimento e Aprendizado"])
app.include_router(reserve.router, prefix=f"{PREFIX}/reserva", tags=["Agente: Produtividade e Agendamento"])
app.include_router(meeting.router, prefix=f"{PREFIX}/meeting", tags=["Agente: Otimização de Reuniões"])
app.include_router(notifications.router, prefix=f"{PREFIX}/notifications", tags=["Comunicação em Tempo Real (WebSocket)"])
app.include_router(chat.router, prefix=f"{PREFIX}/chat", tags=["Agente: Interação com LLM (On-Demand)"])