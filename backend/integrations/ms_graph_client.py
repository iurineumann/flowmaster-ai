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
    
    Abstração: Implementação aqui pode ser facilmente trocada por Google Workspace 
    ou Slack/GitHub API, mantendo a interface (métodos) para o Repositório.
    """
    
    def __init__(self, access_token: str):
        """O token é específico para o usuário autenticado e já inclui o Consentimento."""
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        self.http_client = httpx.AsyncClient(base_url=MS_GRAPH_BASE_URL)

    async def get_recent_emails_and_chats(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Simula a busca real de e-mails, chats e reuniões para o usuário.
        
        Compliance: O acesso só é possível se o 'access_token' tiver o escopo 
        (consentimento) adequado.
        """
        print(f"📡 [MS GRAPH] Buscando dados reais para o usuário {user_id}...")
        
        # Aqui, faríamos chamadas assíncronas reais:
        # 1. messages = await self.http_client.get(f"/users/{user_id}/messages?...")
        # 2. chats = await self.http_client.get(f"/chats?...")
        
        # Por enquanto, retornamos um MOCK para manter o fluxo do Repositório:
        await asyncio.sleep(0.1) # Simula a latência da rede
        
        # Simula o MOCK que será processado pelo Repositório
        from ..services.graph_repository import MOCK_RAW_DATA 
        
        # Em produção: Implementaríamos a tradução do formato MS Graph para RawContextItem.
        return [item.dict() for item in MOCK_RAW_DATA]

    async def close(self):
        """Fecha a sessão HTTP assíncrona."""
        await self.http_client.close()