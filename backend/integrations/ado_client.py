# backend/integrations/ado_client.py

import httpx
from typing import List, Dict, Any, Optional

class ADOClient:
    """
    Cliente assíncrono para interagir com a API REST do Azure DevOps.
    """
    
    def __init__(self, access_token: str, organization_url: str):
        if not organization_url.startswith("https://dev.azure.com/"):
            raise ValueError("URL da Organização ADO inválida.")
            
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json;api-version=7.0"
        }
        self.client = httpx.AsyncClient(base_url=organization_url, headers=self.headers, timeout=10.0)

    async def get_work_items_for_user(self, project_name: str, user_email: str) -> List[Dict[str, Any]]:
        """
        Busca Work Items (Bugs, Tasks) atribuídos a um usuário em um projeto.
        """
        # 1. Constrói a Query WIQL (Work Item Query Language)
        wiql_query = {
            "query": f"SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType] "
                     f"FROM WorkItems "
                     f"WHERE [System.AssignedTo] = '{user_email}' "
                     f"AND [System.State] <> 'Closed' AND [System.State] <> 'Done' "
                     f"ORDER BY [System.ChangedDate] DESC"
        }
        
        try:
            # 2. Executa a query WIQL
            response_wiql = await self.client.post(f"/{project_name}/_apis/wit/wiql", json=wiql_query)
            response_wiql.raise_for_status()
            work_item_refs = response_wiql.json().get("workItems", [])
            
            if not work_item_refs:
                return []

            # 3. Extrai os IDs
            ids = [ref['id'] for ref in work_item_refs[:20]] # Limita a 20 itens
            ids_str = ",".join(map(str, ids))

            # 4. Busca os detalhes completos dos IDs
            response_details = await self.client.get(f"/_apis/wit/workitems?ids={ids_str}&$expand=all")
            response_details.raise_for_status()
            
            work_items = response_details.json().get("value", [])
            return work_items

        except httpx.HTTPStatusError as e:
            print(f"❌ [ADO Client] Falha HTTP: {e.response.status_code} - {e.response.text}")
            raise e
        except Exception as e:
            print(f"❌ [ADO Client] Erro: {e}")
            raise e

    async def close(self):
        await self.client.aclose()

    async def get_projects(self) -> List[Dict[str, Any]]:
        """
        Lista projetos da organização ADO.
        Retorna a lista bruta de projetos (cada item contém pelo menos 'id' e 'name').
        """
        try:
            # Endpoint de projects
            response = await self.client.get("/_apis/projects?api-version=7.0")
            response.raise_for_status()
            data = response.json()
            projects = data.get("value", [])
            return projects
        except httpx.HTTPStatusError as e:
            print(f"❌ [ADO Client] Falha HTTP ao listar projetos: {e.response.status_code} - {e.response.text}")
            raise e
        except Exception as e:
            print(f"❌ [ADO Client] Erro ao listar projetos: {e}")
            raise e