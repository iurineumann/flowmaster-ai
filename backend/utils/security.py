# backend/utils/security.py

import os
import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException, Depends, status
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from ..db.database import get_db
from ..services.config_repository import ConfigRepository
from ..db.models import UserModel
# ✅ Garanta que este import existe:
from .authlib_client import oauth 

# --- Configurações de Segurança ---
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T")
ALGORITHM = "HS256"
AUDIENCE = os.environ.get("JWT_AUDIENCE", "flowmaster-ai-api")

# --- Configuração Microsoft (Apenas para OBO/Refresh) ---
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("MSGRAPH_TENANT_ID", "common")
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# --- Criptografia ---
FERNET_KEY = os.environ.get("FERNET_KEY", "")
if not FERNET_KEY:
    FERNET_KEY = Fernet.generate_key().decode()
cipher_suite = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)

def encrypt_token(token: str) -> str:
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

# --- Hashing de Senha ---
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- Tokens Internos ---
def create_token(user_id: int) -> str:
    to_encode = {
        "user_id": user_id,
        "aud": AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def validate_and_decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=AUDIENCE)
        user_id_raw = payload.get("user_id") or payload.get("sub")
        if user_id_raw is None:
            raise HTTPException(status_code=401, detail="Token inválido.")
        return int(user_id_raw)
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Token inválido.")

# --- Lógica Authlib ---
async def update_user_from_authlib(
    token_data: Dict[str, Any], 
    user_info: Dict[str, Any], 
    db: Session
) -> Optional[UserModel]:
    """Processa login do Authlib e salva refresh token."""
    refresh_token = token_data.get("refresh_token")
    
    oid = user_info.get("oid")
    email = user_info.get("email") or user_info.get("preferred_username")
    name = user_info.get("name")

    if not oid or not email:
        raise HTTPException(status_code=400, detail="Dados de usuário incompletos.")

    repo = ConfigRepository(db)
    user = db.query(UserModel).filter(UserModel.microsoft_id == oid).first()
    
    if not user:
        user = repo.get_user_by_username(email)

    if not user:
        random_pass = get_password_hash(os.urandom(20).hex())
        user = UserModel(
            username=email, email=email, microsoft_id=oid, full_name=name,
            hashed_password=random_pass, is_active=True
        )
        db.add(user)
    else:
        user.microsoft_id = oid
        user.full_name = name
    
    if refresh_token:
        user.entra_refresh_token = encrypt_token(refresh_token)
        user.entra_refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=90)

    db.commit()
    db.refresh(user)
    repo.ensure_user_config_exists(user.id)
    return user

def authenticate_user(username: str, password: str, db: Session) -> Optional[UserModel]:
    user = ConfigRepository(db).get_user_by_username(username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None

# --- Dependências ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_token_from_header(token: str = Depends(oauth2_scheme)) -> str:
    return token

def get_current_user_id(internal_token: str = Depends(get_token_from_header), db: Session = Depends(get_db)) -> int:
    user_id = validate_and_decode_token(internal_token)
    # Apenas retorna o ID para uso leve
    return user_id

# ✅ NOVA FUNÇÃO: Retorna o objeto UserModel completo (Necessária para context.py e skill.py)
def get_current_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> UserModel:
    user = ConfigRepository(db).get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user

# --- Acesso OBO ---
async def get_delegated_access_token(user_id: int, scope: str, db: Session) -> str:
    repo = ConfigRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user or not user.entra_refresh_token:
         raise HTTPException(status_code=401, detail="Reautenticação necessária.")
    
    try:
        refresh_token = decrypt_token(user.entra_refresh_token)
    except:
        raise HTTPException(status_code=401, detail="Token inválido.")

    async with httpx.AsyncClient() as client:
        resp = await client.post(TOKEN_URL, data={
            "client_id": AZURE_CLIENT_ID,
            "client_secret": AZURE_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": scope
        })
        if resp.is_error:
             raise HTTPException(status_code=401, detail="Falha ao renovar token.")
        tokens = resp.json()
    
    if new_rt := tokens.get("refresh_token"):
        user.entra_refresh_token = encrypt_token(new_rt)
        db.commit()
        
    return tokens["access_token"]

async def get_graph_token(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> str:
    return await get_delegated_access_token(user_id, os.environ.get("MSGRAPH_SCOPE", "https://graph.microsoft.com/.default"), db)

async def get_ado_token(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> str:
    return await get_delegated_access_token(user_id, os.environ.get("ADO_SCOPE", "499b84ac-1321-427f-aa17-267ca6975798/.default"), db)