# backend/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import AuthlibBaseError

from ..db.database import get_db
from ..utils.authlib_client import oauth 
# ✅ O import deve ser APENAS estes:
from ..utils.security import (
    create_token,
    update_user_from_authlib,
    authenticate_user,
    get_current_user_id,
)
from ..services.config_repository import ConfigRepository

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    
class RevokeRequest(BaseModel):
    reason: Optional[str] = "Logout manual"

@router.get("/entra/authorize", tags=["Autenticação"])
async def start_entra_flow(request: Request, redirect_uri: str = Query(...)):
    request.session.clear()
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@router.post("/entra/callback", response_model=TokenResponse, tags=["Autenticação"])
async def entra_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token_data = await oauth.microsoft.authorize_access_token(request)
        user_info = await oauth.microsoft.parse_id_token(request, token_data)
    except AuthlibBaseError as e:
        raise HTTPException(status_code=401, detail=f"Erro Authlib: {e}")
    except Exception as e:
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