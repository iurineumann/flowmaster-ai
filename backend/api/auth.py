# backend/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import AuthlibBaseError
import logging

from ..db.database import get_db
from ..utils.authlib_client import oauth 
from ..utils.security import (
    create_token,
    update_user_from_authlib,
    authenticate_user,
    get_current_user_id,
)
from ..services.config_repository import ConfigRepository

# Configurar logging (opcional, mas melhor prática)
logger = logging.getLogger(__name__)

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    
class RevokeRequest(BaseModel):
    reason: Optional[str] = "Logout manual"

@router.get("/entra/authorize", tags=["Autenticação"])
async def start_entra_flow(request: Request, redirect_uri: str = Query(...)):
    # Limpa a sessão antes de iniciar um novo fluxo
    request.session.clear()
    # Authlib define o state/PKCE na sessão e redireciona.
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@router.post("/entra/callback", response_model=TokenResponse, tags=["Autenticação"])
async def entra_callback(request: Request, db: Session = Depends(get_db)):
    
    try:
        # LOGGING SEGURO: Apenas para ver se o state chegou na Query String
        state_param = request.query_params.get("state")

        print("="*50)
        print("DEBUG AUTH CALLBACK - ENTRADA")
        print(f"URL: {request.url}")
        print(f"Method: {request.method}")
        print(f"State from Query Params: {state_param}")
        print("="*50)
        
        # ✅ Authlib lê automaticamente:
        # - state da Query String (Onde está agora no frontend corrigido)
        # - code do Body JSON
        # - state do Cookie (o que resolvemos com o proxy)
        token_data = await oauth.microsoft.authorize_access_token(request)
        user_info = await oauth.microsoft.parse_id_token(request, token_data)
        
        # DEBUG SUCESSO (Se for bem-sucedido)
        print("="*50)
        print("DEBUG AUTH CALLBACK - SUCESSO NA TROCA DE CÓDIGO/TOKEN")
        print(f"User Name: {user_info.get('name')}")
        print("="*50)

    except AuthlibBaseError as e:
        # Erro Authlib (inclui mismatching_state)
        print("="*50)
        print(f"DEBUG AUTH CALLBACK - FALHA Authlib: {e}")
        print("="*50)
        raise HTTPException(status_code=401, detail=f"Erro Authlib: {e}")
    except Exception as e:
        # Erro de rede/outros
        print("="*50)
        print(f"DEBUG AUTH CALLBACK - ERRO INTERNO: {e}")
        print("="*50)
        raise HTTPException(status_code=500, detail="Erro interno no callback.")
    
    user = await update_user_from_authlib(token_data, user_info, db)
    if not user:
        raise HTTPException(status_code=401, detail="Falha ao processar usuário.")

    request.session.clear()
    return TokenResponse(access_token=create_token(user.id), user_id=user.id)

# ... (Rotas /token e /revoke padrão) ...
@router.post("/token", response_model=TokenResponse, tags=["Autenticação"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    return TokenResponse(access_token=create_token(user.id), user_id=user.id)

@router.post("/revoke", status_code=204, tags=["Autenticação"])
async def revoke_refresh_token(request: RevokeRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = ConfigRepository(db).get_user_by_id(user_id)
    if user and user.entra_refresh_token:
        user.entra_refresh_token = None
        db.commit()
    return None