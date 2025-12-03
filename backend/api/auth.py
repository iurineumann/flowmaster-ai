# backend/api/auth.py

import os
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import AuthlibBaseError
# Cliente Async para troca manual
from authlib.integrations.httpx_client import AsyncOAuth2Client 
# Decodificação manual do token
from jose import jwt 

from ..db.database import get_db
# Importamos DEFAULT_SCOPES para garantir que pedimos o id_token
from ..utils.authlib_client import oauth, DEFAULT_SCOPES 
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

        # 2. Validar CSRF (Cookie vs State)
        session_key = f'_state_microsoft_{state}'
        session_data = request.session.get(session_key)

        if not session_data:
            print(f"ERRO: Sessão não encontrada para a chave {session_key}")
            # Debug das chaves disponíveis (apenas para dev)
            print(f"Chaves na sessão: {list(request.session.keys())}")
            raise HTTPException(status_code=400, detail="Sessão inválida ou expirada (CSRF mismatch).")

        # 3. Extrair Code Verifier
        data_internal = session_data.get('data', {})
        code_verifier = data_internal.get('code_verifier')
        
        if not code_verifier:
            print("ERRO: Code Verifier não encontrado na sessão.")
            raise HTTPException(status_code=400, detail="Falha no fluxo PKCE.")

        # 4. Troca Manual de Token
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
                print("ERRO CRÍTICO: id_token não retornado pela Microsoft.")
                raise HTTPException(status_code=500, detail="Microsoft não retornou id_token.")

            print("DEBUG: Token data recebido com sucesso.")
            
            # ✅ CORREÇÃO: Decodificação manual do ID Token
            # Evita o erro da biblioteca Authlib/Starlette ao tentar validar sessão automaticamente
            try:
                id_token_str = token_data.get('id_token')
                # Decodifica sem verificar assinatura (confiamos no canal TLS direto com a Microsoft)
                claims = jwt.get_unverified_claims(id_token_str)
                
                # Normaliza para o formato esperado pelo update_user_from_authlib
                user_info = {
                    'oid': claims.get('oid'),
                    'email': claims.get('email') or claims.get('preferred_username'),
                    'name': claims.get('name'),
                    'preferred_username': claims.get('preferred_username')
                }
                print(f"DEBUG: Token decodificado para: {user_info.get('email')}")
                
            except Exception as e:
                print(f"ERRO AO DECODIFICAR TOKEN: {e}")
                raise HTTPException(status_code=500, detail="Falha ao processar ID Token.")

        # 5. Atualizar/Criar Usuário no Banco
        print("DEBUG: Iniciando atualização do usuário no banco...")
        try:
            user = await update_user_from_authlib(token_data, user_info, db)
            if not user:
                raise ValueError("Falha ao criar instância do usuário.")
            print(f"DEBUG: Usuário salvo/atualizado com ID: {user.id}")
            
        except Exception as db_error:
            print(f"ERRO DE BANCO DE DADOS: {db_error}")
            traceback.print_exc()
            try:
                db.rollback()
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Erro ao salvar usuário: {str(db_error)}")

        request.session.clear()
        return TokenResponse(access_token=create_token(user.id), user_id=user.id)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG AUTH CALLBACK - ERRO GERAL: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ... (Restante do arquivo permanece igual)
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