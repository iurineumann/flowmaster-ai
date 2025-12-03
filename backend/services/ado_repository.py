# backend/services/ado_repository.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..integrations.ado_client import ADOClient
import httpx
import os 

from sqlalchemy.orm import Session
from ..services.config_repository import ConfigRepository
from ..db.models import UserModel

# --- Modelos de Dados (Schemas do ADO) ---
class AdoWorkItem(BaseModel):
    id: int
    type: str # Bug, Task, etc.
    title: str
    state: str
    url: str
    project: str
    organization: str

# --- Repositório ADO ---
class AdoRepository:
    def __init__(self, db: Session, access_token: str = None):
        self.db = db
        self.access_token = access_token
        self.config_repo = ConfigRepository(db) # ✅ Inicialização correta
        self.base_url = "[https://dev.azure.com](https://dev.azure.com)"

    async def get_work_items_for_user(self, user_id: int):
        """
        Busca tasks do usuário.
        Se access_token estiver presente, tenta buscar da API da MS.
        Caso contrário, busca do cache local/banco ou retorna vazio.
        """
        # Exemplo de lógica híbrida
        if not self.access_token:
            # Tenta buscar do banco local se já sincronizado
            # return self.db.query(AdoWorkItem).filter(...).all()
            return []
        
        user = self.config_repo.get_user_by_id(user_id)
        if not user or not user.email:
            print("⚠️ [ADO Repo] Usuário não tem e-mail registrado, não é possível buscar work items.")
            return []

        user_email = user.email
        all_work_items = []
        
        # 1. Busca conexões ADO ativas (Orgs)
        connections = self.config_repo.get_ado_connections(user_id)

        for conn in connections:
            org_url = conn.organization_url
            org_name = org_url.split('/')[-1] # Extrai nome da Org
            
            client = None # Define o cliente fora do try para o finally
            try:
                client = ADOClient(self.access_token, org_url)
                
                # 2. Busca projetos ativos para esta conexão
                projects = self.config_repo.get_ado_projects_for_connection(conn.id)
                if not projects:
                    print(f"ℹ️ [ADO Repo] Nenhum projeto configurado para {org_name}. Pulando.")
                    continue

                for proj in projects:
                    print(f"📡 [ADO Repo] Buscando work items em {org_name}/{proj.project_name} para {user_email}...")
                    items = await client.get_work_items_for_user(proj.project_name, user_email)
                    
                    for item in items:
                        all_work_items.append(
                            AdoWorkItem(
                                id=item['id'],
                                type=item['fields']['System.WorkItemType'],
                                title=item['fields']['System.Title'],
                                state=item['fields']['System.State'],
                                url=item['_links']['html']['href'],
                                project=proj.project_name,
                                organization=org_name
                            )
                        )
            
            except Exception as e:
                print(f"❌ [ADO Repo] Falha ao processar organização {org_url}: {e}")
            
            finally:
                if client:
                    await client.close()
        
        return all_work_items