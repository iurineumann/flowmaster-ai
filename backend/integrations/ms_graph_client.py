# backend/integrations/ms_graph_client.py

import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MSGraphClient:
    def __init__(self, access_token: str):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_upcoming_meetings(self, limit: int = 5):
        """
        Busca as próximas reuniões do calendário do usuário.
        """
        try:
            # Define janela de tempo: Agora até +7 dias
            now = datetime.utcnow().isoformat() + "Z"
            end = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
            
            url = f"{self.base_url}/me/calendarView?startDateTime={now}&endDateTime={end}&$top={limit}&$orderby=start/dateTime"
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers)
                
                if resp.status_code != 200:
                    logger.error(f"Erro MS Graph ({resp.status_code}): {resp.text}")
                    return []
                
                data = resp.json()
                return data.get("value", [])

        except Exception as e:
            logger.error(f"Falha na conexão com MS Graph: {e}")
            return []

    async def get_user_profile(self):
        """Busca dados básicos do perfil (Cargo, Departamento)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/me", headers=self.headers)
                return resp.json() if resp.status_code == 200 else {}
        except:
            return {}