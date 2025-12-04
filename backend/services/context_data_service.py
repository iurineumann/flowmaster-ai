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

        # Inicializa variáveis padrão para evitar quebra no frontend
        tasks_summary = []
        
        try:
            # Tenta buscar tasks se houver configuração
            tasks = await self.ado_repo.get_work_items_for_user(user.id)
            tasks_summary = [
                {"id": t.id, "title": t.title, "status": t.state} 
                for t in tasks[:5]
            ]
        except Exception as e:
            print(f"Erro ao buscar tasks para contexto: {e}")

        # Retorna estrutura compatível com ContextoAgregadoResponse
        return {
            "usuario": user.full_name or user.email,
            "funcao": "Desenvolvedor", # Placeholder ou vir do Graph
            "projeto_atual": tasks[0].project if tasks else "Nenhum ativo",
            "sprint_atual": "Sprint 24", # Placeholder
            "tarefas_pendentes": len(tasks),
            "proxima_reuniao": None, 
            "alertas": []
        }

def get_context_data_service(db: Session = Depends(get_db)) -> ContextDataService:
    return ContextDataService(db)