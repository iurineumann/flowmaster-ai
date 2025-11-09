# backend/main.py (VERSÃO FINAL PARA CI/CD)

from fastapi import FastAPI
from datetime import datetime

# Importa todos os roteadores implementados (Agentes e Configuração)
from backend.api import context
from backend.api import skill 
from backend.api import reserve 
from backend.api import config 

app = FastAPI(title="FlowMaster AI Backend Core", version="0.1.0")

# 1. Rota raiz (Status)
@app.get("/")
def read_root():
    """Endpoint de teste para verificar se o backend está ativo."""
    return {"app_name": "FlowMaster AI", 
            "status": "online", 
            "timestamp": datetime.now().isoformat(),
            "docs": "/docs"}

# 2. Inclusão do Roteador de Configuração
app.include_router(config.router, prefix="/config", tags=["Configuração do Sistema"])

# 3. Inclusão dos Roteadores dos Agentes
app.include_router(context.router, prefix="/contexto", tags=["Contexto e Produtividade"])
app.include_router(skill.router, prefix="/skill", tags=["Desenvolvimento e Aprendizado"])
app.include_router(reserve.router, prefix="/reserva", tags=["Produtividade e Agendamento"])