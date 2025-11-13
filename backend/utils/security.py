# backend/utils/security.py (ATUALIZADO PARA LOGIN)

import os
from fastapi import Header, HTTPException, Depends, status, WebSocket, Query 
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import ValidationError

from sqlalchemy.orm import Session
from ..db.database import get_db
from ..services.config_repository import ConfigRepository # Importa o Repositório
from ..db.models import UserModel # Importa o modelo de DB

# --- Configurações de Segurança ---
# Chave Secreta Padronizada para Desenvolvimento
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T")
ALGORITHM = "HS256"
AUDIENCE = os.environ.get("JWT_AUDIENCE", "flowmaster-ai-api")

# Hashing de Senha
# --- Hashing de Senha (Do passo anterior) ---
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
# ---------------------------------------------


# --- FUNÇÃO CORE: Extração e Validação do Token (REUSÁVEL) ---
def validate_and_decode_token(token: str) -> int:
    """Decodifica e valida o JWT, retornando o user_id."""
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM], 
            audience=AUDIENCE
        )
        user_id_raw = payload.get("user_id") or payload.get("sub")
        
        if user_id_raw is None:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token não contém o identificador do usuário (user_id/sub)."
            )
            
        return int(user_id_raw)

    except (JWTError, ValidationError, ValueError) as e:
        # Re-lança como HTTPException para ser capturado por FastAPI/Starlette
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado. Erro: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Dependência 1: HTTP Header (Para rotas REST) ---
async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Extrai e valida o JWT do cabeçalho 'Authorization' (Para rotas HTTP/REST)."""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    scheme, _, token = authorization.partition(" ")
    
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use 'Bearer <TOKEN>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return validate_and_decode_token(token) # Usa a função CORE

# --- Dependência 2: WebSocket Query Parameter (CRÍTICA PARA O FIX) ---
async def get_user_id_from_websocket_token(
    websocket: WebSocket,
    token: str = Query(...) # Extrai o 'token' do parâmetro de query
) -> int:
    """Extrai e valida o JWT do parâmetro de query 'token' (Para rotas WebSocket)."""
    try:
        user_id = validate_and_decode_token(token)
        return user_id
    except HTTPException as e:
        # Fecha a conexão explicitamente com o código de rejeição 1008
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        # Re-lança para que o Starlette/FastAPI registre o erro
        raise

# --- Autenticação Real (Usando o DB) ---

def authenticate_user(username: str, password: str, db: Session) -> Optional[UserModel]:
    """
    Função REAL que verifica as credenciais do usuário contra o banco de dados.
    """
    repo = ConfigRepository(db)
    
    # 1. Busca o usuário pelo nome de usuário
    user = repo.get_user_by_username(username)
    
    if not user:
        return None # Usuário não encontrado

    # 2. Verifica a senha hasheada
    if verify_password(password, user.hashed_password):
        return user # Sucesso na autenticação
        
    return None # Senha incorreta

# --- Geração de Token ---

def create_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um JWT assinado com o user_id e expiração."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Padrão: Expira em 24h
        expire = datetime.now(timezone.utc) + timedelta(hours=24) 
        
    to_encode = {
        "user_id": user_id,
        "aud": AUDIENCE,
        "exp": expire.timestamp() # Deve ser um timestamp
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependência de Validação de Token (JWT -> User ID) ---

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """
    Dependência do FastAPI para extrair e validar o JWT, retornando o user_id.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Espera-se o formato "Bearer <TOKEN>"
    scheme, _, token = authorization.partition(' ')

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use 'Bearer <TOKEN>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM], 
            audience=AUDIENCE
        )
        
        user_id_raw = payload.get("user_id")
        
        if user_id_raw is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token não contém o identificador do usuário (user_id/sub)."
            )
            
        try:
            user_id = int(user_id_raw)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="O ID do usuário no token é inválido."
            )
        
        return user_id

    except JWTError as e:
        # Inclui verificações de expiração, assinatura inválida, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado. Erro: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Mantenha esta função para o WebSocket (que usa query param)
# MOCK DE TOKEN - NÃO É MAIS USADO NA VERSÃO FINAL
# def create_mock_token(user_id: int) -> str:
#     ...
# --- Função de Geração de Token (Apenas para MOCK no desenvolvimento) ---

def create_mock_token(user_id: int) -> str:
    """Gera um token mockado para testes no ambiente de desenvolvimento."""
    to_encode = {
        "user_id": user_id,
        "aud": AUDIENCE,
        "exp": datetime.now() + timedelta(hours=24) # Expira em 24h
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Adicionamos imports para o mock
from datetime import datetime, timedelta

# --- Função de Geração de Token (Apenas para MOCK no desenvolvimento) ---
def create_mock_token(user_id: int) -> str:
    """Gera um token mockado para testes no ambiente de desenvolvimento."""
    # ... [corpo da função] ...

# NOVO: Função de Dependência para obter Mock Access Token
async def get_access_token_mock() -> str:
    """
    Simula a obtenção do token de acesso do MS Graph.
    """
    # Usando o valor padrão encontrado na implementação
    return "MOCK_ACCESS_TOKEN_FOR_FLOWMASTER_AI"