# backend/main.py

import os
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from backend.services.vector_db_service import vector_db

# Importação dos roteadores
from backend.api import (
    context, 
    skill, 
    reserve, 
    meeting, 
    chat, 
    config, 
    ado, 
    auth, 
    ado_config # ✅ Adicionado
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FlowMaster AI API", version="1.0.0")

# Middleware de Proxy (HTTPS)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Sessão
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T"),
    https_only=False, 
    same_site="lax"
)

# CORS
origins = ["*", "http://localhost:3000", "https://ubuntu:3000", "http://ubuntu:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"], 
)

Instrumentator().instrument(app).expose(app)

# Rotas
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(config.router, prefix="/api/v1/config")
app.include_router(context.router, prefix="/api/v1/contexto")
app.include_router(skill.router, prefix="/api/v1/skill")
app.include_router(reserve.router, prefix="/api/v1/reserva")
app.include_router(meeting.router, prefix="/api/v1/meeting")
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(ado.router, prefix="/api/v1/ado")
app.include_router(ado_config.router, prefix="/api/v1/config/ado")

@app.get("/api/v1/health", tags=["Infra"])
def health_check():
    return {"status": "ok"}