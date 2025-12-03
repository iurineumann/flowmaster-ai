# backend/api/auth.py

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import AuthlibBaseError
# Cliente Async para troca manual
from authlib.integrations.httpx_client import AsyncOAuth2Client 

from ..db.database import get_db
from ..utils.authlib_client import oauth, DEFAULT_SCOPES # Importamos os escopos
from ..utils.security import (
    create_token,
    update_user_from_authlib,
    authenticate_user,
    get_current_user_id,
)
from ..services.config_repository import ConfigRepository

# Configuração de Logger
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
    request.session.clear()
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@router.post("/entra/callback", response_model=TokenResponse, tags=["Autenticação"])
async def entra_callback(request: Request, db: Session = Depends(get_db)):
    
    try:
        # 1. Recuperar parâmetros
        state = request.query_params.get("state")
        body = await request.json()
        code = body.get("code")
        redirect_uri_frontend = body.get("redirect_uri")

        print("="*50)
        print(f"DEBUG MANUAL CALLBACK: Code={code[:10]}... State={state}")

        # 2. Validar CSRF manualmente checando a sessão
        session_key = f'_state_microsoft_{state}'
        session_data = request.session.get(session_key)

        if not session_data:
            print(f"ERRO: Sessão não encontrada para a chave {session_key}")
            # Debug das chaves disponíveis (segurança em dev)
            print(f"Chaves na sessão: {list(request.session.keys())}")
            raise HTTPException(status_code=400, detail="Sessão inválida ou expirada (CSRF mismatch).")

        # 3. Extrair o Code Verifier (PKCE)
        data_internal = session_data.get('data', {})
        code_verifier = data_internal.get('code_verifier')
        
        if not code_verifier:
            print("ERRO: Code Verifier não encontrado na sessão.")
            raise HTTPException(status_code=400, detail="Falha no fluxo PKCE.")

        # 4. Trocar o código pelo token MANUALMENTE
        metadata = await oauth.microsoft.load_server_metadata()
        token_endpoint = metadata['token_endpoint']
        
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        
        # ✅ CORREÇÃO: Construir string de escopos para garantir id_token
        scope_str = " ".join(DEFAULT_SCOPES)

        async with AsyncOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            code_challenge_method='S256',
            scope=scope_str # Importante passar o escopo aqui também
        ) as client:
            
            # ✅ CORREÇÃO: Passar 'scope' explicitamente no fetch_token
            token_data = await client.fetch_token(
                token_endpoint,
                code=code,
                redirect_uri=redirect_uri_frontend, 
                code_verifier=code_verifier,
                grant_type='authorization_code',
                scope=scope_str 
            )
            
            # Debug para confirmar o recebimento do id_token
            print(f"DEBUG TOKEN KEYS: {list(token_data.keys())}")
            print(f"DEBUG TOKEN DATA: {token_data}")
            print(f"DEBUG USER INFO: {token_data.get('id_token')}")
            
            if 'id_token' not in token_data:
                raise HTTPException(status_code=500, detail="Microsoft não retornou id_token.")

            # Parse do ID Token
            user_info = await oauth.microsoft.parse_id_token(request, token_data)
            
            print(f"DEBUG: Login bem-sucedido para {user_info.get('email')}")

    except Exception as e:
        print(f"DEBUG AUTH CALLBACK - ERRO: {e}")
        # Retorna o erro real para o frontend ver
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    
    # 5. Finalizar Login
    user = await update_user_from_authlib(token_data, user_info, db)
    if not user:
        raise HTTPException(status_code=401, detail="Falha ao processar usuário.")

    request.session.clear()
    return TokenResponse(access_token=create_token(user.id), user_id=user.id)

# ... (Rotas /token e /revoke permanecem iguais)
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