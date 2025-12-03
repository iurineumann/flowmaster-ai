# backend/services/ado_repository.py

from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel # ✅ Necessário para o response_model do FastAPI

from .config_repository import ConfigRepository
from ..integrations.ado_client import ADOClient
from ..db.models import UserModel

# ✅ CORREÇÃO: Transformado em Pydantic Model
class AdoWorkItem(BaseModel):
    id: int
    title: str
    state: str
    type: str
    url: str
    project: str
    organization: str

class AdoRepository:
    def __init__(self, db: Session, access_token: str = None):
        self.db = db
        self.access_token = access_token
        self.base_url = "https://dev.azure.com"
        self.config_repo = ConfigRepository(db)

    async def get_work_items_for_user(self, user_id: int) -> List[AdoWorkItem]:
        if not self.access_token:
            return []
            
        try:
            user = self.config_repo.get_user_by_id(user_id)
            if not user or not user.email:
                return []

            connections = self.config_repo.get_ado_connections(user_id)
            all_items = []

            for conn in connections:
                try:
                    client = ADOClient(self.access_token, conn.organization_url)
                    # Em produção real, aqui buscaríamos os projetos do banco
                    # Para evitar erro se não houver projetos configurados, usamos um default ou passamos vazio
                    projects = self.config_repo.get_ado_projects_for_connection(conn.id)
                    
                    # Se a lista de projetos estiver vazia, o client pode não ter o que buscar.
                    # Vamos assumir que o client tem um método de descoberta ou iterar se houver projetos.
                    for proj in projects:
                        items = await client.get_work_items_for_user(proj.project_name, user.email)
                        for i in items:
                            all_items.append(AdoWorkItem(
                                id=i.get('id'),
                                title=i['fields'].get('System.Title', 'Sem título'),
                                state=i['fields'].get('System.State', 'Unknown'),
                                type=i['fields'].get('System.WorkItemType', 'Item'),
                                url=i['_links']['html']['href'] if '_links' in i else '',
                                project=proj.project_name,
                                organization=conn.organization_url.split('/')[-1]
                            ))
                    await client.close()
                except Exception as e:
                    print(f"Erro ADO Repo para conexão {conn.id}: {e}")
                    continue

            return all_items
            
        except Exception as e:
            print(f"Erro geral no ADO Repo: {e}")
            return []