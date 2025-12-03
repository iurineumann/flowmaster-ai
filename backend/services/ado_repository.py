# backend/services/ado_repository.py

from sqlalchemy.orm import Session
from typing import List
# Import dos modelos necessários
from ..db.models import UserModel
from .config_repository import ConfigRepository 
from ..integrations.ado_client import ADOClient

class AdoWorkItem:
    # Definição simples para tipagem interna, ou use Pydantic se preferir
    def __init__(self, id, title, state, type, url, project, organization):
        self.id = id
        self.title = title
        self.state = state
        self.type = type
        self.url = url
        self.project = project
        self.organization = organization

class AdoRepository:
    def __init__(self, db: Session, access_token: str = None):
        self.db = db
        self.access_token = access_token
        self.base_url = "https://dev.azure.com"
        # ✅ CORREÇÃO: Inicialização do config_repo
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
                # Lógica real de conexão com o Client
                try:
                    client = ADOClient(self.access_token, conn.organization_url)
                    # Busca projetos configurados ou todos
                    projects = self.config_repo.get_ado_projects_for_connection(conn.id)
                    
                    # Se não houver projetos específicos, pule ou busque default (simplificado)
                    for proj in projects:
                        items = await client.get_work_items_for_user(proj.project_name, user.email)
                        for i in items:
                            all_items.append(AdoWorkItem(
                                id=i['id'],
                                title=i['fields']['System.Title'],
                                state=i['fields']['System.State'],
                                type=i['fields']['System.WorkItemType'],
                                url=i['_links']['html']['href'],
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