# backend/utils/security.py (CORRIGIDO COM ASYNC/AWAIT)

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
AZURE_VALID_ISSUERS = [
    f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
    f"https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0", # MSA (Pessoal)
    f"https://login.microsoftonline.com/common/v2.0"
]
AZURE_CLIENT_ID = os.environ.get("MSGRAPH_CLIENT_ID")
AZURE_CLIENT_SECRET = os.environ.get("MSGRAPH_CLIENT_SECRET")
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

JWKS_CACHE = None

# --- Hashing de Senha ---
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- Geração/Validação de Token INTERNO ---
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
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (sem ID).")
        return int(user_id_raw)
    except (JWTError, ValidationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token inválido: {str(e)}")

# --- Validação Token Entra ID ---
async def fetch_jwks(max_retries: int = 3, initial_delay: float = 1.0):
    """
    Busca JWKS da Microsoft com retry logic e exponential backoff.
    
    Args:
        max_retries: Número máximo de tentativas
        initial_delay: Atraso inicial em segundos (será multiplicado por 2 a cada tentativa)
    """
    global JWKS_CACHE
    if JWKS_CACHE is not None:
        return JWKS_CACHE
    
    import asyncio
    
    for attempt in range(max_retries):
        try:
            print(f"📡 [JWKS] Tentativa {attempt + 1}/{max_retries} de buscar chaves da Microsoft...")
            async with httpx.AsyncClient() as client:
                response = await client.get(AZURE_JWKS_URL, timeout=10)
                response.raise_for_status()
                JWKS_CACHE = response.json()
                print(f"✅ [JWKS] Chaves da Microsoft carregadas com sucesso.")
                return JWKS_CACHE
        except httpx.TimeoutException as e:
            print(f"⏱️ [JWKS] Timeout na tentativa {attempt + 1}: {e}")
        except httpx.HTTPStatusError as e:
            print(f"❌ [JWKS] Erro HTTP {e.response.status_code} na tentativa {attempt + 1}: {e}")
        except Exception as e:
            print(f"❌ [JWKS] Erro inesperado na tentativa {attempt + 1}: {e}")
        
        # Se não foi a última tentativa, aguarda antes de retry
        if attempt < max_retries - 1:
            delay = initial_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            print(f"⏳ [JWKS] Aguardando {delay}s antes da próxima tentativa...")
            await asyncio.sleep(delay)
    
    print(f"❌ [JWKS] Falha ao buscar chaves da Microsoft após {max_retries} tentativas.")
    return None

async def decode_and_validate_entra_token(token: str) -> Dict[str, Any]: # ✅ Rota deve ser 'async def'
    """Decodifica e valida o JWT do Microsoft Entra ID."""
    try:
        jwks = await fetch_jwks() # ✅ CORREÇÃO: 'await'
        if not jwks:
            raise HTTPException(status_code=503, detail="Não foi possível validar o token com a Microsoft.")
        
        payload = jwt.decode(
            token,
            key=jwks,
            algorithms=["RS256"],
            audience=AZURE_CLIENT_ID,
            options={"verify_signature": True, "verify_aud": True, "verify_iss": False}
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token Entra ID inválido: {str(e)}")


# --- Autenticação e Vínculo de Contas ---
async def authenticate_user_entra_id(token: str, db: Session) -> Optional[UserModel]: # ✅ Rota deve ser 'async def'
    """
    Valida o token do Entra ID e registra/atualiza o usuário na base de dados (JIT).
    """
    payload = await decode_and_validate_entra_token(token) # ✅ CORREÇÃO: 'await'
    
    entra_oid = payload.get("oid") 
    email = payload.get("preferred_username") or payload.get("email")
    name = payload.get("name")

    if not entra_oid or not email:
        raise HTTPException(status_code=400, detail="Token incompleto (sem OID ou Email).")

    repo = ConfigRepository(db)
    
    user = db.query(UserModel).filter(UserModel.microsoft_id == entra_oid).first()
    
    if user:
        if user.email != email: user.email = email
        db.commit()
        return user

    user = repo.get_user_by_username(email) 
    
    if user:
        print(f"🔗 [Auth] Vinculando conta existente {email} ao Microsoft ID {entra_oid}")
        user.microsoft_id = entra_oid
        user.email = email
        db.commit()
        return user

    print(f"🆕 [Auth] Criando novo usuário via Entra ID: {email}")
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
    
    repo.ensure_user_config_exists(new_user.id)
    
    return new_user

def authenticate_user(username: str, password: str, db: Session) -> Optional[UserModel]:
    repo = ConfigRepository(db)
    user = repo.get_user_by_username(username)
    if not user: return None
    if verify_password(password, user.hashed_password): return user
    return None

# --- Dependências de Injeção (Depends) ---
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token") 

def get_token_from_header(token: str = Depends(oauth2_scheme)) -> str:
    return token

def get_current_user_id(
    internal_token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> int:
    user_id = validate_and_decode_token(internal_token)
    repo = ConfigRepository(db)
    if not repo.get_user_by_id(user_id):
         raise HTTPException(status_code=404, detail="Usuário do token não encontrado.")
    return user_id

async def get_user_id_from_websocket_token( # ✅ Rota deve ser 'async def'
    websocket: WebSocket,
    token: str = Query(...)
) -> int:
    try:
        return validate_and_decode_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise

# --- Tokens de Acesso a Serviços (Mocks e Reais) ---

async def get_access_token_mock() -> str:
    return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"

async def get_real_access_token(scope: str) -> str:
    """
    Executa o fluxo Client Credentials para obter um Access Token (MS Graph ou ADO).
    """
    if not all([TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET]):
        print(f"⚠️ [Entra ID] Credenciais incompletas (Client Credentials) para scope {scope}. Usando Mock.")
        return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV" 
        
    print(f"📡 [Entra ID] Buscando token real (Client Credentials) para scope: {scope}")
    
    token_data = {
        "client_id": AZURE_CLIENT_ID,
        "scope": scope,
        "client_secret": AZURE_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        # ✅ CORREÇÃO: Cliente HTTP criado no contexto da função
        async with httpx.AsyncClient() as client:
            response = await client.post(TOKEN_URL, data=token_data)
            response.raise_for_status()
            token_json = response.json()
        
        access_token = token_json.get("access_token")
        
        if not access_token:
            raise ValueError(f"Resposta do Entra ID não contém 'access_token' para scope {scope}.")
            
        print(f"✅ [Entra ID] Token de acesso (Client Credentials) real obtido para scope {scope}.")
        return access_token

    except httpx.HTTPStatusError as e:
        print(f"❌ [Entra ID Error] Falha de HTTP: {e.response.text}. Retornando Mock.")
        return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"
    except Exception as e:
        print(f"❌ [Entra ID Error] Erro inesperado ao obter token: {e}. Retornando Mock.")
        return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"

# --- Dependências de Token de Serviço (para Injeção nas Rotas) ---

async def get_graph_token() -> str:
    """Dependência injetável para obter um token do MS Graph."""
    scope = os.environ.get("MSGRAPH_SCOPE", "https://graph.microsoft.com/.default")
    return await get_real_access_token(scope=scope)

async def get_ado_token() -> str:
    """Dependência injetável para obter um token do Azure DevOps."""
    scope = os.environ.get("ADO_SCOPE", "499b84ac-1321-427f-aa17-267ca6975798/.default")
    return await get_real_access_token(scope=scope)