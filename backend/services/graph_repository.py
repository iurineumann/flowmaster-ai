# backend/services/graph_repository.py

from sqlalchemy.orm import Session
from ..integrations.ms_graph_client import MSGraphClient
from ..utils.security import decrypt_token

class GraphRepository:
    def __init__(self, db: Session, access_token: str = None):
        self.db = db
        self.access_token = access_token
        # Em um cenário real OBO, o token já vem injetado. 
        # Se não vier, teríamos que tentar recuperar do banco (refresh token), 
        # mas o fluxo atual injeta via dependência 'get_graph_token'.

    async def get_calendar_events(self):
        if not self.access_token:
            return []
        
        client = MSGraphClient(self.access_token)
        events = await client.get_upcoming_meetings()
        
        # Simplifica o objeto para consumo interno
        return [
            {
                "subject": e.get("subject"),
                "start": e.get("start", {}).get("dateTime"),
                "end": e.get("end", {}).get("dateTime"),
                "is_online": e.get("isOnlineMeeting", False),
                "organizer": e.get("organizer", {}).get("emailAddress", {}).get("name")
            }
            for e in events
        ]

    async def get_user_role(self):
        if not self.access_token:
            return "Usuário"
        
        client = MSGraphClient(self.access_token)
        profile = await client.get_user_profile()
        return profile.get("jobTitle", "Colaborador")