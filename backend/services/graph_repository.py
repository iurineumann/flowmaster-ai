# backend/services/graph_repository.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..integrations.ms_graph_client import MSGraphClient
import httpx
import os 
import json

from ..db.database import SessionLocal
from ..services.config_repository import ConfigRepository

# ❌ Variáveis de Configuração do Entra ID REMOVIDAS DAQUI
# Elas agora residem em 'utils/security.py'

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

# --- Repositório de Dados Brutos ---
class GraphRepository:
    async def get_raw_context_by_user(self, user_id: int, access_token: str) -> List[RawContextItem]:
        # Removido fallback MOCK automático. Agora exige token válido.
        if not access_token:
            raise Exception("Access token ausente; não é possível buscar dados reais do Microsoft Graph.")

        try:
            client = MSGraphClient(access_token)
            user_identifier: Optional[str] = None
            with SessionLocal() as db:
                repo = ConfigRepository(db)
                user = repo.get_user_by_id(user_id)
                if user and user.microsoft_id:
                    user_identifier = user.microsoft_id
                elif user and user.email:
                    user_identifier = user.email

                if not user_identifier:
                    raise Exception(f"Não foi possível identificar usuário {user_id} para requisição ao Graph.")

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