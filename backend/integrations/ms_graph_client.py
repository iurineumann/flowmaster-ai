# backend/integrations/ms_graph_client.py

from typing import List, Dict, Any
from datetime import datetime
import asyncio
import httpx # Usaremos httpx para requisições assíncronas (FastAPI padrão)

# --- Configurações de API Externa ---
MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

class MSGraphClient:
    """
    Cliente para interagir com o Microsoft Graph (ou qualquer API externa).
    """
    
    def __init__(self, access_token: str):
        """O token é específico para o usuário autenticado e já inclui o Consentimento."""
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        self.http_client = httpx.AsyncClient(base_url=MS_GRAPH_BASE_URL)

    # ✅ CORREÇÃO: Alterado de user_id: int para user_identifier: str (Email ou OID)
    async def get_recent_emails_and_chats(self, user_identifier: str) -> List[Dict[str, Any]]:
        """
        Simula a busca real de e-mails, chats e reuniões para o usuário.
        """
        print(f"📡 [MS GRAPH] Buscando dados reais para o usuário: {user_identifier}...")
        
        # Executa as buscas em paralelo
        emails_task = self._fetch_emails(user_identifier)
        chats_task = self._fetch_chats(user_identifier)
        
        results = await asyncio.gather(emails_task, chats_task, return_exceptions=True)
        
        combined_items = []
        
        if isinstance(results[0], list):
            combined_items.extend(results[0])
        else:
            print(f"❌ [MS Graph] Erro ao buscar e-mails: {results[0]}")

        if isinstance(results[1], list):
            combined_items.extend(results[1])
        else:
            print(f"⚠️ [MS Graph] Erro/Aviso ao buscar chats: {results[1]}")

        combined_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return combined_items

    async def _fetch_emails(self, user_identifier: str) -> List[Dict[str, Any]]:
        """Busca os últimos 10 e-mails da caixa de entrada usando o OID ou UPN."""
        endpoint = f"/users/{user_identifier}/messages"
        params = {
            "$top": 10,
            "$select": "id,receivedDateTime,subject,bodyPreview,from",
            "$orderby": "receivedDateTime DESC"
        }
        
        try:
            response = await self.http_client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            items = [self._normalize_email_item(msg) for msg in data.get("value", [])]
            return items
        except httpx.HTTPStatusError as e:
            print(f"❌ [MS Graph] Falha HTTP em Emails: {e.response.status_code} - {e.response.text}")
            raise e

    async def _fetch_chats(self, user_identifier: str) -> List[Dict[str, Any]]:
        """Busca os últimos 5 chats. Requer permissão Chat.Read.All."""
        endpoint = f"/users/{user_identifier}/chats"
        params = {
            "$top": 5,
            "$expand": "lastMessagePreview",
            "$orderby": "lastUpdatedDateTime DESC"
        }
        
        try:
            response = await self.http_client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            items = []
            for chat in data.get("value", []):
                if chat.get("lastMessagePreview"):
                    items.append(self._normalize_chat_item(chat))
            return items
        except httpx.HTTPStatusError as e:
            print(f"⚠️ [MS Graph] Falha HTTP em Chats (pode ser permissão): {e.response.status_code}")
            raise e

    # ... (O restante das funções _normalize_ e _extract_project_tag permanece o mesmo) ...
    def _normalize_email_item(self, msg: Dict) -> Dict[str, Any]:
        subject = msg.get("subject", "Sem Assunto")
        body = msg.get("bodyPreview", "")
        sender = msg.get("from", {}).get("emailAddress", {}).get("address", "Desconhecido")
        return {
            "item_id": msg.get("id"), "item_type": "email", "source": "Outlook",
            "timestamp": msg.get("receivedDateTime"), "subject_or_title": subject,
            "sender_or_creator": sender, "project_tag": self._extract_project_tag(subject, body),
            "content_preview": body
        }

    def _normalize_chat_item(self, chat: Dict) -> Dict[str, Any]:
        last_msg = chat.get("lastMessagePreview", {})
        body = last_msg.get("body", {}).get("content", "")
        sender = last_msg.get("from", {}).get("user", {}).get("displayName", "Desconhecido")
        topic = chat.get("topic") or f"Chat com {sender}"
        return {
            "item_id": chat.get("id"), "item_type": "chat", "source": "Teams",
            "timestamp": last_msg.get("createdDateTime"), "subject_or_title": topic,
            "sender_or_creator": sender, "project_tag": self._extract_project_tag(topic, body),
            "content_preview": body
        }

    def _extract_project_tag(self, title: str, content: str) -> str:
        text = (str(title) + " " + str(content)).upper()
        if "CLIENTE_X" in text: return "CLIENTE_X"
        if "PROJETO_Y" in text: return "PROJETO_Y"
        if "CRITICO" in text or "URGENTE" in text: return "GERAL_CRITICO"
        return "GERAL"

    async def close(self):
        await self.http_client.aclose()