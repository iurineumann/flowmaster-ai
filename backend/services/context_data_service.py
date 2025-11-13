# backend/services/context_data_service.py

from typing import List, Optional
from ..services.graph_repository import GraphRepository, RawContextItem 

class ContextDataService:
    
    def __init__(self, repo: GraphRepository):
        self.repo = repo
        self.foco_critico_tag = "CLIENTE_X"
        
    async def get_all_raw_context(self, user_id: int, access_token: str) -> List[RawContextItem]:
        return await self.repo.get_raw_context_by_user(user_id, access_token)

    async def get_critical_context(self, user_id: int, access_token: str) -> Optional[RawContextItem]:
        all_raw_data = await self.get_all_raw_context(user_id, access_token)
        
        itens_do_foco = [
            item for item in all_raw_data 
            if item.project_tag == self.foco_critico_tag
        ]
        
        return itens_do_foco[0] if itens_do_foco else None

def get_context_data_service() -> ContextDataService:
    return ContextDataService(repo=GraphRepository())