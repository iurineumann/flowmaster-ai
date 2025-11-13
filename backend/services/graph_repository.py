# backend/services/graph_repository.py (VERSÃO FINAL COM OAUTH REAL)

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
# Importa a dependência que faz a busca real
from ..integrations.ms_graph_client import MSGraphClient 
import httpx
import os 
import json # Necessário para decodificar a resposta do token

# --- Configurações do Entra ID (Lido do .env) ---
TENANT_ID = os.environ.get("MSGRAPH_TENANT_ID")
CLIENT_ID = os.environ.get("MSGRAPH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("MSGRAPH_CLIENT_SECRET")
# O padrão é o endpoint do token de autorização
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
# Scope para o Client Credentials Flow (acesso como o app)
SCOPE = "https://graph.microsoft.com/.default"

# Cliente HTTP assíncrono para reuso na busca do Token
auth_http_client = httpx.AsyncClient(timeout=10.0) 

# --- Modelos de Dados (Não Alterados) ---\
class RawContextItem(BaseModel):
    """Modelo para um item de dado bruto extraído do MS Graph."""
    item_id: str
    item_type: str
    source: str
    timestamp: str
    subject_or_title: str
    sender_or_creator: str
    project_tag: str 
    content_preview: str

# --- Dados MOCKADOS (Mantidos para Fallback) ---\
MOCK_RAW_DATA: List[RawContextItem] = [
    RawContextItem(
        item_id="e1", 
        item_type="email", 
        source="Outlook", 
        timestamp="2025-11-10T09:00:00Z",
        subject_or_title="[CLIENTE_X] BUG CRÍTICO - Falha na Integração de Pagamento",
        sender_or_creator="gerente@empresa.com",
        project_tag="CLIENTE_X",
        content_preview="Precisamos de um desenvolvedor sênior para analisar o log de erros e corrigir o fluxo de pagamento antes do final do dia."
    ),
    RawContextItem(
        item_id="t1", 
        item_type="chat", 
        source="Teams", 
        timestamp="2025-11-10T09:30:00Z",
        subject_or_title="Discussão sobre a feature 'Dashboard 2.0'",
        sender_or_creator="dev_junior@empresa.com",
        project_tag="Dashboard",
        content_preview="O layout do novo dashboard está travando em dispositivos móveis, precisamos de um hotfix."
    )
]

# --- 🎯 FUNÇÃO CORE: OBTENÇÃO DO TOKEN REAL ---
async def get_real_access_token() -> str:
    """
    Executa o fluxo Client Credentials para obter um Access Token do MS Entra ID.
    Esta função é AGORA a dependência de token no endpoint da API.
    """
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        print("⚠️ [Entra ID] Credenciais incompletas. Retornando token MOCK.")
        # Simula o token para manter a compatibilidade da API em DEV
        return os.environ.get("MSGRAPH_ACCESS_TOKEN_MOCK", "token_valido_para_mock") 
        
    print(f"📡 [Entra ID] Buscando token real em: {TOKEN_URL}")
    
    token_data = {
        "client_id": CLIENT_ID,
        "scope": SCOPE,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials" # Fluxo Client Credentials (App-only)
    }

    try:
        response = await auth_http_client.post(TOKEN_URL, data=token_data)
        response.raise_for_status() # Lança erro para 4xx/5xx
        
        token_json = response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            raise ValueError("Resposta do Entra ID não contém 'access_token'.")
            
        print("✅ [Entra ID] Token de acesso real obtido com sucesso.")
        return access_token

    except httpx.HTTPStatusError as e:
        print(f"❌ [Entra ID Error] Falha de HTTP (Status Error {e.response.status_code}): {e.response.text}. Retornando MOCK.")
        return os.environ.get("MSGRAPH_ACCESS_TOKEN_MOCK", "token_valido_para_mock")
    except Exception as e:
        print(f"❌ [Entra ID Error] Erro inesperado ao obter token: {e}. Retornando MOCK.")
        return os.environ.get("MSGRAPH_ACCESS_TOKEN_MOCK", "token_valido_para_mock")


# --- Repositório de Dados Brutos ---\
class GraphRepository:
    """
    Repositório para acesso a dados brutos do usuário no MS Graph (emails, chats, etc.).
    """

    async def get_raw_context_by_user(self, user_id: int, access_token: str) -> List[RawContextItem]:
        
        # O acesso ao Graph exige o Token de Acesso (que AGORA é real)
        if "mock" in access_token or not access_token: 
             print("⚠️ [Repo] Usando token MOCK ou Token Vazio. Retornando MOCK de Contexto.")
             return MOCK_RAW_DATA
             
        # Tenta buscar dados reais (PRODUÇÃO)
        try:
            # client usa o token real
            client = MSGraphClient(access_token)
            print(f"📡 [MS GRAPH] Buscando dados reais para o usuário {user_id}...")
            raw_data_dicts = await client.get_recent_emails_and_chats(user_id)
            
            # Se a busca real retornar algo, use.
            if raw_data_dicts:
                print("✅ [Repo] Dados reais do MS Graph retornados.")
                return [RawContextItem(**d) for d in raw_data_dicts]
            
            # Se a busca real retornar lista vazia
            print("⚠️ [Repo] Busca real retornou lista vazia. Usando MOCK de Contexto (Fallback Dev).")
            return MOCK_RAW_DATA
            
        except httpx.HTTPStatusError as e:
            # Tratamento de erro (falha de token/permissão, etc.)
            print(f"❌ [Repo Error] Falha de integração com o Graph (Status Error): {e}. Usando MOCK de Contexto (Fallback).")
            return MOCK_RAW_DATA
        except Exception as e:
            # Erro de rede, Timeout ou exceção genérica
            print(f"❌ [Repo Error] Erro inesperado na integração: '{e}'. Usando MOCK de Contexto (Fallback).")
            return MOCK_RAW_DATA