# backend/utils/security.py (ATUALIZADO COM VÍNCULO DE CONTAS)

import os
import httpx
from fastapi import Header, HTTPException, Depends, status, WebSocket, Query 
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import ValidationError

from sqlalchemy.orm import Session
from ..db.database import get_db
from ..services.config_repository import ConfigRepository 
from ..db.models import UserModel 

# --- Configurações de Segurança ---
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T")
ALGORITHM = "HS256"
AUDIENCE = os.environ.get("JWT_AUDIENCE", "flowmaster-ai-api")

# --- Configuração MSAL / Entra ID ---
TENANT_ID = os.environ.get("MSGRAPH_TENANT_ID", "common") 
AZURE_JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
# Valid issuers podem variar dependendo do tipo de conta (organizacional vs pessoal)
AZURE_VALID_ISSUERS = [
    f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
    f"https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0", # MSA (Personal)
    f"https://login.microsoftonline.com/common/v2.0"
]
AZURE_CLIENT_ID = os.environ.get("MSGRAPH_CLIENT_ID") 

# Cache para as chaves públicas (JWKS)
JWKS_CACHE = None

# --- Hashing de Senha ---
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- FUNÇÕES CORE ---

def create_token(user_id: int) -> str:
    to_encode = {
        "user_id": user_id,
        "aud": AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def validate_and_decode_token(token: str) -> int:
    """Decodifica e valida o JWT INTERNO, retornando o user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=AUDIENCE)
        user_id_raw = payload.get("user_id") or payload.get("sub")
        if user_id_raw is None:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (sem ID).")
        return int(user_id_raw)
    except (JWTError, ValidationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token inválido: {str(e)}")

# --- Validação Entra ID ---

async def fetch_jwks():
    global JWKS_CACHE
    if JWKS_CACHE is None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(AZURE_JWKS_URL, timeout=10)
                response.raise_for_status()
                JWKS_CACHE = response.json()
        except Exception as e:
            print(f"❌ Erro ao buscar chaves da Microsoft: {e}")
            # Em ambiente DEV offline, isso pode falhar. O ideal é tratar ou mockar se necessário.
            return None
    return JWKS_CACHE

async def decode_and_validate_entra_token(token: str) -> Dict[str, Any]:
    """Valida o token OIDC da Microsoft."""
    jwks = await fetch_jwks()
    if not jwks:
        # Fallback para dev se não conseguir conectar na Microsoft (opcional)
        # Em produção isso deve falhar.
        raise HTTPException(status_code=503, detail="Não foi possível validar o token com a Microsoft.")

    try:
        payload = jwt.decode(
            token,
            key=jwks,
            algorithms=["RS256"],
            audience=AZURE_CLIENT_ID,
            options={"verify_signature": True, "verify_aud": True, "verify_iss": False} # Issuer check relaxado para multi-tenant
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token Entra ID inválido: {str(e)}")


# --- Autenticação e Vínculo de Contas ---

async def authenticate_user_entra_id(token: str, db: Session) -> Optional[UserModel]:
    """
    Autentica via Entra ID. 
    Se o usuário existe (por OID ou Email), faz o login/link.
    Se não, cria um novo usuário (JIT).
    """
    payload = await decode_and_validate_entra_token(token)
    
    # Extrai dados do token
    entra_oid = payload.get("oid") # ID Imutável
    email = payload.get("preferred_username") or payload.get("email")
    name = payload.get("name")

    if not entra_oid or not email:
        raise HTTPException(status_code=400, detail="Token incompleto (sem OID ou Email).")

    repo = ConfigRepository(db)
    
    # 1. Tenta achar pelo ID da Microsoft (Vínculo Forte)
    user = db.query(UserModel).filter(UserModel.microsoft_id == entra_oid).first()
    
    if user:
        # Atualiza o email se mudou
        if user.email != email:
            user.email = email
            db.commit()
        return user

    # 2. Se não achou pelo ID, tenta achar pelo Email (Vínculo Suave)
    user = repo.get_user_by_username(email) # Assume que username = email
    
    if user:
        # VINCULAR CONTA: Achou o email, mas não tinha o ID da Microsoft. Salva agora.
        print(f"🔗 [Auth] Vinculando conta existente {email} ao Microsoft ID {entra_oid}")
        user.microsoft_id = entra_oid
        user.email = email
        db.commit()
        return user

    # 3. Novo Usuário (Registro JIT)
    print(f"🆕 [Auth] Criando novo usuário via Entra ID: {email}")
    # Gera senha aleatória pois o login será sempre via Microsoft
    random_pass = get_password_hash(os.urandom(20).hex())
    
    new_user = UserModel(
        username=email,
        email=email,
        microsoft_id=entra_oid,
        full_name=name,
        hashed_password=random_pass,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Garante config inicial
    repo.ensure_user_config_exists(new_user.id)
    
    return new_user

# --- Dependências ---

async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> int:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Token ausente.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Token malformado.")
    return validate_and_decode_token(token)

async def get_user_id_from_websocket_token(
    websocket: WebSocket,
    token: str = Query(...)
) -> int:
    try:
        return validate_and_decode_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise

# --- Mock ---
async def get_access_token_mock() -> str:
    return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"

# Fallback para login manual (devuser)
def authenticate_user(username: str, password: str, db: Session) -> Optional[UserModel]:
    repo = ConfigRepository(db)
    user = repo.get_user_by_username(username)
    if not user: return None
    if verify_password(password, user.hashed_password): return user
    return None