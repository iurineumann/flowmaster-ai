# backend/api/auth.py (NOVO MÓDULO DE AUTENTICAÇÃO)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any

# Importa as novas funções de segurança
from ..utils.security import create_token, authenticate_user 

from sqlalchemy.orm import Session # NOVO: Importa a Session
from ..db.database import get_db # NOVO: Importa o get_db

from ..utils.security import create_token, authenticate_user

router = APIRouter()

# --- Schemas de Resposta (Pydantic) ---

class TokenResponse(BaseModel):
    """Esquema de resposta para o login."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    # Opcional: tempo de expiração
    # expires_in: int 

# --- Rota de Login (POST) ---

@router.post("/token", response_model=TokenResponse, tags=["Autenticação"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db) # NOVO: Injeta a sessão do DB
):
    """
    Recebe as credenciais (username/password) e retorna o JWT assinado.
    """
    # 1. Autenticação (passa o objeto DB)
    user = authenticate_user(form_data.username, form_data.password, db) # DB passado aqui!
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas: Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Geração do Token (usa user.id real)
    access_token = create_token(user_id=user.id)
    
    # 3. Retorno
    return {
        "access_token": access_token, 
        "user_id": user.id,
        "token_type": "bearer"
    }