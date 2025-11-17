# backend/main.py

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
from backend.api import auth
from backend.api import admin
from backend.api import ado # ✅ NOVO: Agente ADO
from backend.api import ado_config # ✅ NOVO: Configuração ADO

# --- Variáveis de Configuração ---
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", 
    "http://localhost:5173,http://localhost:3000"
).split(",")

print(f"✅ [CORS] Configurado para permitir origens: {ALLOWED_ORIGINS}")

# --- Inicialização do FastAPI ---
app = FastAPI(title="FlowMaster AI Backend Core", version="0.1.0")

# --- MIDDLEWARE: CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# ✅ NOVAS ROTAS ADO
app.include_router(ado_config.router, prefix=f"{PREFIX}/config/ado", tags=["Configuração: Azure DevOps"])
app.include_router(ado.router, prefix=f"{PREFIX}/ado", tags=["Agente: Azure DevOps"])