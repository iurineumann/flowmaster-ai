# backend/initial_data_mock.py

from sqlalchemy.orm import Session
from .db.models import SystemModuleDetailModel

def init_system_data(db: Session):
    """
    Popula o banco de dados com os Módulos de IA do Sistema.
    Define quais CARDS aparecem no Dashboard.
    """
    # ✅ LISTA COMPLETA DE MÓDULOS (Versão 3.0)
    modules = [
        {
            "id": "context_agent",
            "name": "Contexto & Foco",
            "description": "Analisa suas tarefas e define sua prioridade atual.",
            "api_endpoint": "/contexto/agregado",
            "grid_column_span": 2 # Card largo
        },
        {
            "id": "skill_agent",
            "name": "Mentor de Skills",
            "description": "Recomendações de aprendizado priorizadas por criticidade.",
            "api_endpoint": "/skill/sugestoes",
            "grid_column_span": 1
        },
        {
            "id": "reserve_agent",
            "name": "Gestor de Recursos",
            "description": "Sugestão inteligente de salas e equipamentos.",
            "api_endpoint": "/reserva/sugestao",
            "grid_column_span": 1
        },
        {
            "id": "meeting_agent",
            "name": "Facilitador de Reuniões",
            "description": "Detecta bloqueios e sugere alinhamentos.",
            "api_endpoint": "/meeting/sugestao",
            "grid_column_span": 1
        },
        {
            "id": "ado_agent",
            "name": "Monitor Azure DevOps",
            "description": "Visão em tempo real do seu board.",
            "api_endpoint": "/ado/work_items",
            "grid_column_span": 2 # Card largo
        }
    ]

    print("⚡ [DB Init] Verificando módulos do sistema...")
    for mod_data in modules:
        existing = db.query(SystemModuleDetailModel).filter_by(id=mod_data["id"]).first()
        if not existing:
            print(f"   -> Criando módulo novo: {mod_data['name']}")
            new_mod = SystemModuleDetailModel(**mod_data)
            db.add(new_mod)
        else:
            # Atualiza propriedades se mudaram (ex: tamanho do grid)
            existing.name = mod_data["name"]
            existing.description = mod_data["description"]
            existing.grid_column_span = mod_data["grid_column_span"]
    
    db.commit()
    print("✅ [DB Init] Todos os módulos sincronizados.")