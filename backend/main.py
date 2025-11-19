# backend/main.py

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.api import context, skill, reserve, meeting, chat, config, ado, auth

app = FastAPI(
    title="FlowMaster AI API",
    version="1.0.0",
)

# --- Configuração de Segurança da Sessão ---
# Em produção (HTTPS), use secure=True e samesite='lax' ou 'strict'.
# Em desenvolvimento (HTTP localhost), secure=False é necessário.
is_production = os.environ.get("ENVIRONMENT") == "production"

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T"),
    https_only=is_production, # False em dev
    same_site="lax"           # 'lax' é geralmente seguro o suficiente e permite redirects
)

# ... (restante do arquivo igual: CORS, Routers, etc.) ...
origins = [
    "*", 
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://ubuntu:5173",
    "http://ubuntu:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(config.router, prefix="/api/v1/config")
app.include_router(context.router, prefix="/api/v1/contexto")
app.include_router(skill.router, prefix="/api/v1/skill")
app.include_router(reserve.router, prefix="/api/v1/reserva")
app.include_router(meeting.router, prefix="/api/v1/meeting")
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(ado.router, prefix="/api/v1/ado")

@app.get("/api/v1/health", tags=["Infra"])
def health_check():
    return JSONResponse({"status": "ok", "version": "1.0.0"})