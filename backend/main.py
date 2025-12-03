import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware # Importante para Nginx/HTTPS

from backend.api import context, skill, reserve, meeting, chat, config, ado, auth

app = FastAPI(
    title="FlowMaster AI API",
    version="1.0.0",
)

# --- Configuração de Segurança de Proxy ---
# Força o FastAPI a confiar nos headers X-Forwarded-Proto do Nginx
# Isso corrige redirecionamentos e cookies seguros atrás do proxy
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# --- Configuração de Segurança da Sessão ---
# Em ambiente Docker/Proxy, 'lax' é geralmente o melhor compromisso
is_production = os.environ.get("ENVIRONMENT") == "production"

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T"),
    https_only=False, # Deixe False; o Nginx trata o SSL e o ProxyHeadersMiddleware cuida do resto
    same_site="lax"
)

# Configurações de CORS
origins = [
    "*", 
    "http://localhost:3000",
    "https://ubuntu:3000", # Garanta que seu domínio esteja aqui
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
    return {"status": "ok", "version": "1.0.0"}