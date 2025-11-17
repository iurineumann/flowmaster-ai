# backend/api/auth.py (CORRIGIDO COM ASYNC/AWAIT)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any

from sqlalchemy.orm import Session
from ..db.database import get_db

# Importa as novas funções de segurança
from ..utils.security import create_token, authenticate_user_entra_id, authenticate_user

router = APIRouter()

# --- Schemas de Resposta (Pydantic) ---

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int

class EntraTokenRequest(BaseModel):
    """Esquema para receber o token do Entra ID do frontend."""
    entra_id_token: str

# --- Rota 1: Login via Entra ID (OIDC) ---

@router.post("/entra_login", response_model=TokenResponse, tags=["Autenticação"])
async def login_via_entra_id( # ✅ Rota deve ser 'async def'
    request: EntraTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Recebe o ID Token do Microsoft Entra ID e retorna o JWT INTERNO do FlowMaster.
    """
    # ✅ CORREÇÃO: Adicionado 'await' para a chamada assíncrona
    user = await authenticate_user_entra_id(request.entra_id_token, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falha na validação do Token Entra ID.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Geração do Token INTERNO do FlowMaster (HS256)
    internal_jwt = create_token(user.id)
    
    return TokenResponse(
        access_token=internal_jwt,
        user_id=user.id
    )

# --- Rota 2: Login via Credenciais Locais (Para testes/fallback) ---
@router.post("/token", response_model=TokenResponse, tags=["Autenticação"])
async def login_for_access_token( # ✅ Convertido para 'async def'
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Recebe as credenciais (username/password) e retorna o JWT assinado (Legacy/Mock).
    """
    # HARDCODE PARA DESENVOLVIMENTO: devuser/devpass
    if form_data.username == "devuser" and form_data.password == "devpass":
        print(f"🔐 [Auth] Login de desenvolvimento com devuser detectado...")
        repo = ConfigRepository(db)
        user = repo.get_user_by_username("devuser")
        if not user:
            print(f"🆕 [Auth] Criando usuário de desenvolvimento 'devuser'...")
            hashed_pass = get_password_hash(form_data.password)
            user = UserModel(
                username="devuser",
                email="dev@flowmaster.local",
                hashed_password=hashed_pass,
                full_name="Developer User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            repo.ensure_user_config_exists(user.id)
            print(f"✅ [Auth] Usuário devuser criado com ID: {user.id}")
        else:
            print(f"✅ [Auth] Usuário devuser encontrado com ID: {user.id}")
        internal_jwt = create_token(user.id)
        print(f"✅ [Auth] Token JWT criado para user_id={user.id}")
        return TokenResponse(
            access_token=internal_jwt,
            user_id=user.id
        )
    # Caso contrário, valida normalmente
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        print(f"❌ [Auth] Falha ao autenticar usuário: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas: Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"✅ [Auth] Usuário autenticado: {form_data.username} (ID: {user.id})")
    internal_jwt = create_token(user.id)
    return TokenResponse(
        access_token=internal_jwt,
        user_id=user.id
    )