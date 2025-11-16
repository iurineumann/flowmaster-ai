# backend/services/graph_repository.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..integrations.ms_graph_client import MSGraphClient
import httpx
import os 
import json

from ..db.database import SessionLocal
from ..services.config_repository import ConfigRepository

# --- Configurações do Entra ID (Lido do .env) ---
TENANT_ID = os.environ.get("MSGRAPH_TENANT_ID")
CLIENT_ID = os.environ.get("MSGRAPH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("MSGRAPH_CLIENT_SECRET")
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = "https://graph.microsoft.com/.default"

auth_http_client = httpx.AsyncClient(timeout=10.0) 

# --- Modelos de Dados ---
class RawContextItem(BaseModel):
    item_id: str
    item_type: str
    source: str
    timestamp: str
    subject_or_title: str
    sender_or_creator: str
    project_tag: str 
    content_preview: str

# --- Dados MOCKADOS (Mantidos para Fallback de DEV) ---
MOCK_RAW_DATA: List[RawContextItem] = [
    RawContextItem(
        item_id="e1", item_type="email", source="Outlook", timestamp="2025-11-10T09:00:00Z",
        subject_or_title="[CLIENTE_X] BUG CRÍTICO - Falha na Integração de Pagamento",
        sender_or_creator="gerente@empresa.com", project_tag="CLIENTE_X",
        content_preview="Precisamos de um desenvolvedor sênior para analisar o log de erros e corrigir o fluxo de pagamento antes do final do dia."
    ),
    RawContextItem(
        item_id="t1", item_type="chat", source="Teams", timestamp="2025-11-10T09:30:00Z",
        subject_or_title="Discussão sobre a feature 'Dashboard 2.0'",
        sender_or_creator="dev_junior@empresa.com", project_tag="Dashboard",
        content_preview="O layout do novo dashboard está travando em dispositivos móveis, precisamos de um hotfix."
    )
]

# --- Função de Token REAL ---
async def get_real_access_token() -> str:
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        print("⚠️ [Entra ID] Credenciais incompletas (Client Credentials). Usando Mock.")
        return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV" 
        
    print(f"📡 [Entra ID] Buscando token real (Client Credentials) em: {TOKEN_URL}")
    
    token_data = {
        "client_id": CLIENT_ID,
        "scope": SCOPE,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        response = await auth_http_client.post(TOKEN_URL, data=token_data)
        response.raise_for_status()
        token_json = response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            raise ValueError("Resposta do Entra ID não contém 'access_token'.")
            
        print("✅ [Entra ID] Token de acesso (Client Credentials) real obtido.")
        return access_token

    except httpx.HTTPStatusError as e:
        print(f"❌ [Entra ID Error] Falha de HTTP: {e.response.text}. Retornando Mock.")
        return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"
    except Exception as e:
        print(f"❌ [Entra ID Error] Erro inesperado ao obter token: {e}. Retornando Mock.")
        return "MOCK_MS_GRAPH_ACCESS_TOKEN_FOR_DEV"

# --- Repositório de Dados Brutos ---
class GraphRepository:
    async def get_raw_context_by_user(self, user_id: int, access_token: str) -> List[RawContextItem]:
        
        if "MOCK" in access_token.upper() or not access_token: 
             print("⚠️ [Repo] Usando token MOCK ou Token Vazio. Retornando MOCK de Contexto (Fallback).")
             return MOCK_RAW_DATA
             
        try:
            client = MSGraphClient(access_token)
            
            user_identifier: Optional[str] = None
            with SessionLocal() as db:
                repo = ConfigRepository(db)
                user = repo.get_user_by_id(user_id)
                
                # ✅ CORREÇÃO: Prioriza o OID (microsoft_id) para a chamada da API
                if user and user.microsoft_id:
                    user_identifier = user.microsoft_id
                elif user and user.email:
                    user_identifier = user.email
                
                if not user_identifier:
                    print(f"❌ [Repo] Não foi possível encontrar OID ou Email para user_id {user_id}. Usando MOCK.")
                    return MOCK_RAW_DATA

            print(f"📡 [MS GRAPH] Buscando dados reais para o identificador: {user_identifier}...")
            raw_data_dicts = await client.get_recent_emails_and_chats(user_identifier)
            await client.close()
            
            if raw_data_dicts:
                print(f"✅ [Repo] {len(raw_data_dicts)} itens reais do MS Graph retornados.")
                return [RawContextItem(**d) for d in raw_data_dicts]
            
            print("⚠️ [Repo] Busca real retornou lista vazia. Usando MOCK de Contexto (Fallback Dev).")
            return MOCK_RAW_DATA
            
        except httpx.HTTPStatusError as e:
            print(f"❌ [Repo Error] Falha de integração com o Graph (Status Error): {e}. Usando MOCK de Contexto (Fallback).")
            return MOCK_RAW_DATA
        except Exception as e:
            print(f"❌ [Repo Error] Erro inesperado na integração: '{e}'. Usando MOCK de Contexto (Fallback).")
            return MOCK_RAW_DATA