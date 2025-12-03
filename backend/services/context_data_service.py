# backend/services/context_data_service.py

from sqlalchemy.orm import Session
from fastapi import Depends
from ..db.database import get_db
from ..db.models import UserModel
from ..services.ado_repository import AdoRepository

class ContextDataService:
    def __init__(self, db: Session):
        self.db = db
        self.ado_repo = AdoRepository(db) 

    async def get_aggregated_context(self, user_id: int) -> dict:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return {}

        try:
            tasks = await self.ado_repo.get_work_items_for_user(user.id)
            tasks_summary = [
                {"id": t.id, "title": t.title, "status": t.state} 
                for t in tasks[:5]
            ]
        except Exception:
            tasks_summary = []

        return {
            "user_name": user.full_name,
            "role": "Developer", 
            "active_tasks": tasks_summary,
            "recent_meetings": [], 
            "preferences": {}
        }

# ✅ FUNÇÃO DE INJEÇÃO DE DEPENDÊNCIA (Corrige o ImportError)
def get_context_data_service(db: Session = Depends(get_db)) -> ContextDataService:
    return ContextDataService(db)