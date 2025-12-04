# backend/integrations/ado_client.py

from typing import Any, Dict, List
import httpx
import base64
import logging

logger = logging.getLogger(__name__)

class ADOClient:
    def __init__(self, token: str, organization_url: str, is_pat: bool = False):
        self.base_url = organization_url.rstrip('/')
        
        # Configura Headers de Autenticação
        if is_pat:
            # Para PAT, usa-se Basic Auth com usuário vazio e PAT como senha
            # Codifica ":<PAT>" em Base64
            auth_str = f":{token}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            self.headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/json"
            }
        else:
            # OAuth Token
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

    async def get_work_items_for_user(self, project: str, user_email: str):
        """
        Busca work items atribuídos ao usuário via WIQL.
        """
        try:
            # 1. Executa Query WIQL para pegar IDs
            wiql_url = f"{self.base_url}/{project}/_apis/wit/wiql?api-version=7.1"
            
            query = {
                "query": f"""
                    SELECT [System.Id]
                    FROM WorkItems
                    WHERE [System.AssignedTo] = '{user_email}'
                    AND [System.State] NOT IN ('Closed', 'Done', 'Removed')
                    ORDER BY [System.ChangedDate] DESC
                """
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(wiql_url, json=query, headers=self.headers)
                
                if resp.status_code == 401:
                    logger.warning(f"[(ADO] Falha de Autenticação (401) em {self.base_url}")
                    return []
                if resp.status_code != 200:
                    logger.error(f"[ADO] Erro WIQL {resp.status_code}: {resp.text}")
                    return []
                
                data = resp.json()
                work_items = data.get("workItems", [])
                if not work_items:
                    return []
                
                ids = [str(wi['id']) for wi in work_items[:10]] # Limita a 10
                
                # 2. Busca Detalhes dos IDs
                ids_str = ",".join(ids)
                details_url = f"{self.base_url}/{project}/_apis/wit/workitems?ids={ids_str}&api-version=7.1"
                
                details_resp = await client.get(details_url, headers=self.headers)
                if details_resp.status_code == 200:
                    return details_resp.json().get("value", [])
                
                return []

        except Exception as e:
            logger.error(f"[ADO Client] Erro de conexão: {e}")
            return []

    async def close(self):
        pass
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