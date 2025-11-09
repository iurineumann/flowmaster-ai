# backend/main.py (FINAL - COM TODOS OS AGENTES/ROTAS INCLUÍDOS)
from fastapi import FastAPI
from datetime import datetime

# Importa os roteadores reais de todos os agentes
from backend.api import context
from backend.api import skill 
from backend.api import reserve 

app = FastAPI(title="FlowMaster AI Backend Core", version="0.1.0")

# 1. Rota raiz (Status - MANTIDA)
@app.get("/")
def read_root():
    """Endpoint de teste para verificar se o backend está ativo."""
    return {"app_name": "FlowMaster AI", 
            "status": "online", 
            "timestamp": datetime.now().isoformat(),
            "docs": "/docs"}

# 2. Inclusão dos Roteadores dos Agentes
app.include_router(context.router, prefix="/contexto", tags=["Contexto e Produtividade"])
app.include_router(skill.router, prefix="/skill", tags=["Desenvolvimento e Aprendizado"])
app.include_router(reserve.router, prefix="/reserva", tags=["Recursos e Utilização"])