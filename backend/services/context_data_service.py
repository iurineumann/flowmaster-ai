# backend/services/context_data_service.py

from sqlalchemy.orm import Session
from ..db.models import UserModel
from ..services.ado_repository import AdoRepository
# Se tiver GraphRepository, importe aqui também

class ContextDataService:
    def __init__(self, db: Session):
        self.db = db
        # Instancia repositórios auxiliares
        # Nota: O token será injetado dinamicamente ou recuperado do banco se necessário
        self.ado_repo = AdoRepository(db) 

    async def get_aggregated_context(self, user_id: int) -> dict:
        """
        Reúne dados de várias fontes para alimentar a LLM.
        """
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return {}

        # Busca Tasks do ADO (simulação de chamada interna segura)
        # O AdoRepository deve saber lidar com a falta de token momentânea
        tasks = self.ado_repo.get_work_items_for_user(user.id)
        
        # Formata para a IA
        tasks_summary = [
            {"id": t.id, "title": t.title, "status": t.state} 
            for t in tasks[:5] # Limita a 5 para não estourar contexto
        ]

        return {
            "user_name": user.full_name,
            "role": "Developer", # Idealmente viria do perfil
            "active_tasks": tasks_summary,
            "recent_meetings": [], # Implementar integração com Graph
            "preferences": {}
        }