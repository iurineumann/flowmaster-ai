# backend/services/context_data_service.py

from sqlalchemy.orm import Session
from fastapi import Depends
from ..db.database import get_db
from ..db.models import UserModel
from ..services.ado_repository import AdoRepository

class ContextDataService:
    def __init__(self, db: Session):
        self.db = db
        # O token será injetado dinamicamente no repositório se necessário,
        # ou o repositório gerencia a recuperação via ConfigRepository
        self.ado_repo = AdoRepository(db) 

    async def get_aggregated_context(self, user_id: int) -> dict:
        """
        Agrega dados brutos do usuário para consumo dos Agentes (LLM).
        """
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return {}

        tasks_summary = []
        raw_tasks = []
        
        try:
            # Busca tarefas reais do Azure DevOps
            # O AdoRepository deve lidar com a autenticação interna (tokens salvos)
            raw_tasks = await self.ado_repo.get_work_items_for_user(user.id)
            
            # Formata para a LLM (apenas campos essenciais para economizar tokens)
            tasks_summary = [
                {
                    "id": getattr(t, 'id', 'N/A'), 
                    "title": getattr(t, 'title', 'Sem título'), 
                    "status": getattr(t, 'state', 'Unknown'),
                    "type": getattr(t, 'type', 'Task'),
                    "project": getattr(t, 'project', 'Geral')
                } 
                for t in raw_tasks[:10] # Analisa as top 10 tarefas
            ]
        except Exception as e:
            print(f"⚠️ [ContextData] Erro ao buscar ADO: {e}")

        return {
            "user_name": user.full_name or user.email,
            "role": "Developer", # Pode ser parametrizável no futuro
            "active_tasks": tasks_summary,
            "task_count": len(raw_tasks),
            "recent_meetings": [] # Placeholder para integração futura com Graph
        }

def get_context_data_service(db: Session = Depends(get_db)) -> ContextDataService:
    return ContextDataService(db)