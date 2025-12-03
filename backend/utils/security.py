# backend/utils/security.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from ..db.database import get_db
from ..services.config_repository import ConfigRepository
from ..db.models import UserModel

# Configurações
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "FL0WM4ST3R_AI_D3V_S3CR3T")
ALGORITHM = "HS256"
AUDIENCE = os.environ.get("JWT_AUDIENCE", "flowmaster-ai-api")

# Criptografia
FERNET_KEY = os.environ.get("FERNET_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)

def encrypt_token(token: str) -> str:
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    return cipher_suite.decrypt(encrypted_token.encode()).decode()

# Hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT
def create_token(user_id: int) -> str:
    to_encode = {"user_id": user_id, "aud": AUDIENCE, "exp": datetime.now(timezone.utc) + timedelta(hours=24)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def validate_and_decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=AUDIENCE)
        user_id = payload.get("user_id") or payload.get("sub")
        if user_id is None: raise HTTPException(status_code=401, detail="Token inválido")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Authlib Helper
async def update_user_from_authlib(token_data: Dict, user_info: Dict, db: Session) -> Optional[UserModel]:
    oid = user_info.get("oid")
    email = user_info.get("email") or user_info.get("preferred_username")
    name = user_info.get("name")
    
    if not oid or not email: return None

    repo = ConfigRepository(db)
    user = db.query(UserModel).filter(UserModel.microsoft_id == oid).first()
    if not user: user = repo.get_user_by_username(email)
    
    if not user:
        user = UserModel(username=email, email=email, microsoft_id=oid, full_name=name, hashed_password=get_password_hash("oidc_user"), is_active=True)
        db.add(user)
    else:
        user.microsoft_id = oid
        user.full_name = name
    
    if token_data.get("refresh_token"):
        user.entra_refresh_token = encrypt_token(token_data["refresh_token"])
    
    db.commit()
    db.refresh(user)
    repo.ensure_user_config_exists(user.id)
    return user

def authenticate_user(username: str, password: str, db: Session) -> Optional[UserModel]:
    user = ConfigRepository(db).get_user_by_username(username)
    if user and verify_password(password, user.hashed_password): return user
    return None

# Dependências FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_token_from_header(token: str = Depends(oauth2_scheme)) -> str:
    return token

def get_current_user_id(token: str = Depends(get_token_from_header)) -> int:
    return validate_and_decode_token(token)

# ✅ A FUNÇÃO CRÍTICA QUE ESTAVA FALTANDO
def get_current_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> UserModel:
    user = ConfigRepository(db).get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

# Funções OBO (Placeholder seguro)
async def get_ado_token(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> str:
    # Lógica de refresh OBO viria aqui
    return "mock_ado_token"