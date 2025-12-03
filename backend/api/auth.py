# backend/api/auth.py

import os
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
# Usamos AsyncOAuth2Client para ter controle total do fluxo
from authlib.integrations.httpx_client import AsyncOAuth2Client 
# Decodificação manual do token (Segura pois vem via TLS direto da MS)
from jose import jwt 

from ..db.database import get_db
from ..utils.authlib_client import oauth, DEFAULT_SCOPES 
from ..utils.security import (
    create_token,
    update_user_from_authlib,
    authenticate_user,
    get_current_user_id,
)
from ..services.config_repository import ConfigRepository

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
        # 1. Ler parâmetros (State na Query, Code no Body)
        state = request.query_params.get("state")
        body = await request.json()
        code = body.get("code")
        redirect_uri_frontend = body.get("redirect_uri")

        logger.info(f"Callback iniciado. State: {state}")

        # 2. Validar Sessão (CSRF)
        session_key = f'_state_microsoft_{state}'
        session_data = request.session.get(session_key)

        if not session_data:
            logger.error(f"Sessão não encontrada para chave: {session_key}")
            raise HTTPException(status_code=400, detail="Sessão inválida ou expirada. Tente logar novamente.")

        # 3. Recuperar Code Verifier (PKCE)
        data_internal = session_data.get('data', {})
        code_verifier = data_internal.get('code_verifier')
        
        if not code_verifier:
            logger.error("Code Verifier PKCE ausente na sessão.")
            raise HTTPException(status_code=400, detail="Falha de segurança PKCE.")

        # 4. Troca Manual de Token (Evita erros internos da lib Starlette)
        metadata = await oauth.microsoft.load_server_metadata()
        token_endpoint = metadata['token_endpoint']
        
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        scope_str = " ".join(DEFAULT_SCOPES)

        async with AsyncOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            code_challenge_method='S256',
            scope=scope_str
        ) as client:
            token_data = await client.fetch_token(
                token_endpoint,
                code=code,
                redirect_uri=redirect_uri_frontend, 
                code_verifier=code_verifier,
                grant_type='authorization_code',
                scope=scope_str 
            )
            
            if 'id_token' not in token_data:
                raise HTTPException(status_code=500, detail="Microsoft não retornou o id_token.")

            # 5. Decodificar Dados do Usuário
            try:
                # Decodifica claims sem verificar assinatura (o canal TLS garante a origem)
                claims = jwt.get_unverified_claims(token_data.get('id_token'))
                user_info = {
                    'oid': claims.get('oid'),
                    'email': claims.get('email') or claims.get('preferred_username'),
                    'name': claims.get('name'),
                    'preferred_username': claims.get('preferred_username')
                }
            except Exception as e:
                logger.error(f"Erro ao decodificar ID Token: {e}")
                raise HTTPException(status_code=500, detail="Token inválido recebido do provedor.")

        # 6. Persistir Usuário (Com tratamento de erro de banco)
        try:
            user = await update_user_from_authlib(token_data, user_info, db)
            if not user:
                raise ValueError("Não foi possível criar ou recuperar o usuário.")
        except Exception as db_error:
            logger.error(f"Erro de Banco de Dados ao salvar usuário: {db_error}")
            traceback.print_exc()
            db.rollback() # Garante que a transação não fique travada
            raise HTTPException(status_code=500, detail="Erro ao salvar dados do usuário.")

        request.session.clear()
        return TokenResponse(access_token=create_token(user.id), user_id=user.id)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erro interno não tratado: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

# ... (Rotas padrão mantidas)
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