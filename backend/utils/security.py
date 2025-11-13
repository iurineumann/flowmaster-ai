import os
from fastapi import Header, HTTPException, Depends, status, WebSocket, Query 
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
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

# Hashing de Senha
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- Configuração MSAL / Entra ID ---
# Substitua pelos valores reais do seu App Registration (tenant ID)
TENANT_ID = os.environ.get("AZURE_TENANT_ID", "common") # Use 'common' para tenants multi-organizacionais ou seu tenant ID específico
AZURE_JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
AZURE_VALID_ISSUERS = [
    f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
    f"https://login.microsoftonline.com/common/v2.0" # Issuer para /common
]
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "YOUR_AZURE_CLIENT_ID") 

# Cache para as chaves públicas (JWKS)
JWKS_CACHE = None
# --------------------------------------------

# --- Geração de Tokens (Para o token INTERNO do FlowMaster) ---
def create_token(user_id: int) -> str:
    to_encode = {
        "user_id": user_id,
        "aud": AUDIENCE,
        "exp": datetime.now() + timedelta(hours=24)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- FUNÇÃO CORE: Validação do Token (Entra ID e Interno) ---
async def fetch_jwks():
    """Busca chaves públicas do Entra ID com cache."""
    global JWKS_CACHE
    if JWKS_CACHE is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_JWKS_URL, timeout=5)
            response.raise_for_status()
            JWKS_CACHE = response.json()
    return JWKS_CACHE

def decode_and_validate_entra_token(token: str) -> Dict[str, Any]:
    """Decodifica e valida o JWT do Microsoft Entra ID."""
    try:
        jwks = fetch_jwks() # A chamada deve ser síncrona ou await para garantir o cache
        
        # Faz a decodificação e validação
        payload = jwt.decode(
            token,
            key=jwks,
            algorithms=["RS256"], # Entra ID usa RS256
            audience=[AZURE_CLIENT_ID],
            issuer=AZURE_VALID_ISSUERS,
            options={"verify_signature": True, "verify_aud": True, "verify_iss": True}
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token Entra ID inválido ou expirado. Erro: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar JWKS: {e}",
        )

# --- Dependências de Autenticação ---

# 1. Dependência para Rotas HTTP (JWT Interno)
def get_current_user_id(
    internal_token: str = Depends(get_token_from_header), # Assumindo função utilitária para extrair token do header
    db: Session = Depends(get_db)
) -> int:
    """Valida o token JWT INTERNO do FlowMaster."""
    try:
        # Tenta decodificar o token INTERNO (HS256)
        payload = jwt.decode(internal_token, SECRET_KEY, algorithms=[ALGORITHM], audience=AUDIENCE)
        user_id = payload.get("user_id")
        if user_id is None:
            raise JWTError("Token não contém user_id.")
        
        # Garante que o usuário ainda existe no DB (check de segurança)
        repo = ConfigRepository(db)
        if not repo.get_user_by_id(user_id):
             raise JWTError("Usuário não existe.")

        return int(user_id)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token FlowMaster inválido ou expirado. Erro: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 2. Dependência para WebSockets (Usa Query Param)
def get_user_id_from_websocket_token(
    token: Optional[str] = Query(None, alias="token")
) -> int:
    """Autenticação de WebSocket usando o token interno do FlowMaster."""
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token JWT não fornecido.")
    
    pass


# 3. Autenticação Principal do Entra ID (Para a rota de login)
def authenticate_user_entra_id(token: str, db: Session) -> Optional[UserModel]:
    """
    Valida o token do Entra ID e registra/atualiza o usuário na base de dados (JIT).
    O token passado é o ID Token do OIDC.
    """
    # 1. Validação e Decodificação do Token Entra ID
    payload = decode_and_validate_entra_token(token)
    
    # O email (preferred_username) ou o OID (object ID) são usados como ID único
    user_email = payload.get("preferred_username") or payload.get("email") 
    user_name = payload.get("name") # Nome completo
    user_oid = payload.get("oid") # Object ID (ID único Entra)

    if not user_email:
        # Deve ter pelo menos um ID para registro
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token Entra ID não contém identificador de usuário.")

    repo = ConfigRepository(db)
    
    # 2. Busca o Usuário pelo OID ou Email (LGPD: Usar OID como primary key é preferível)
    user = repo.get_user_by_username(user_email)
    
    if not user:
        # 3. Registro Just-In-Time (JIT)
        # O Entra ID não fornece senha, então setamos a senha como um hash random para cumprir o modelo
        # e usamos o token do Entra para o login.
        print(f"🛠️ [DB] Registrando novo usuário JIT: {user_email}")
        random_hash = get_password_hash(os.urandom(16).hex()) # Senha fake/aleatória
        user = repo.create_user(
            username=user_email,
            hashed_password=random_hash,
            full_name=user_name,
            is_active=True
        )
        
        # 4. Garante as Configurações Iniciais
        repo.ensure_user_config_exists(user.id)
        
    return user

# --- Utilitário de Extração (Deve existir ou ser substituído pela classe OAuth2PasswordBearer) ---
from fastapi.security import OAuth2PasswordBearer

# O token é injetado pelo header 'Authorization: Bearer <token>'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/entra_login") 

def get_token_from_header(token: str = Depends(oauth2_scheme)):
    """Dependência para extrair o token do header de autenticação."""
    return token

async def get_access_token_mock() -> str:
    """
    Simula a obtenção do token de acesso do MS Graph.
    Movido para security.py para centralizar as dependências de segurança.
    """
    # Esta string é usada pelo GraphRepository como um token "válido" para dev.
    return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"