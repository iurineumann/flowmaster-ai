# backend/services/ado_repository.py

from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from .config_repository import ConfigRepository
from ..integrations.ado_client import ADOClient
from ..utils.security import decrypt_token

# Modelo Pydantic para resposta
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
        self.oauth_token = access_token
        self.config_repo = ConfigRepository(db)

    async def get_work_items_for_user(self, user_id: int) -> List[AdoWorkItem]:
        try:
            user = self.config_repo.get_user_by_id(user_id)
            if not user or not user.email:
                return []

            connections = self.config_repo.get_ado_connections(user_id)
            all_items = []

            for conn in connections:
                client = None
                try:
                    # Lógica de Seleção de Token
                    token_to_use = self.oauth_token
                    is_pat = False

                    # Se não temos token OAuth ou ele falhou antes, tentamos o PAT
                    # (Na prática, tentamos o PAT se ele existir, pois é mais confiável para dados específicos)
                    if conn.personal_access_token:
                        try:
                            token_to_use = decrypt_token(conn.personal_access_token)
                            is_pat = True
                        except:
                            print(f"Erro ao descriptografar PAT para {conn.organization_url}")

                    # Se não temos nenhum token, pulamos
                    if not token_to_use:
                        continue

                    client = ADOClient(token_to_use, conn.organization_url, is_pat=is_pat)
                    
                    # Projetos (Busca default se não configurado)
                    projects = self.config_repo.get_ado_projects_for_connection(conn.id)
                    if not projects:
                        # Fallback: Tenta projeto padrão ou infere (simulado aqui como 'FlowMasterAI' ou similar)
                        # O ideal seria listar projetos, mas vamos assumir um padrão ou lista vazia
                        pass

                    # Itera sobre projetos configurados
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

                except Exception as e:
                    print(f"Erro ADO Repo para conexão {conn.id}: {e}")
                finally:
                    if client: await client.close()

            return all_items
            
        except Exception as e:
            print(f"Erro geral no ADO Repo: {e}")
            return []