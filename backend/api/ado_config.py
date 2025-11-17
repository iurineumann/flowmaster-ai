# backend/api/ado_config.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db.database import get_db
from ..services.config_repository import ConfigRepository
from ..utils.security import get_current_user_id, get_ado_token
from ..api.schemas import AdoConnection, AdoConnectionCreate, AdoProject, AdoProjectCreate

router = APIRouter()

# --- Endpoints de Configuração do ADO ---

@router.post("/connections", response_model=AdoConnection, status_code=status.HTTP_201_CREATED)
async def create_ado_connection(
    conn_in: AdoConnectionCreate,
    user_id: int = Depends(get_current_user_id),
    ado_token: str = Depends(get_ado_token),
    db: Session = Depends(get_db)
):
    """Cria uma nova conexão de Organização ADO para o usuário."""
    repo = ConfigRepository(db)
    try:
        conn = repo.create_ado_connection(user_id, conn_in.organization_url)

        # Sincroniza projetos imediatamente (se possível)
        try:
            await repo.sync_ado_projects_for_connection(conn.id, conn.organization_url, ado_token)
        except Exception as e:
            print(f"⚠️ [ADO Config] Falha ao sincronizar projetos após criação da conexão: {e}")

        return conn
    except IntegrityError: # Captura violação de UniqueConstraint
        raise HTTPException(status_code=400, detail="Esta organização já está cadastrada.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar conexão: {e}")

@router.get("/connections", response_model=List[AdoConnection])
async def get_user_ado_connections(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Lista as conexões ADO ativas de um usuário."""
    repo = ConfigRepository(db)
    return repo.get_ado_connections(user_id)

@router.post("/projects", response_model=AdoProject, status_code=status.HTTP_201_CREATED)
async def add_ado_project(
    project_in: AdoProjectCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Adiciona um novo projeto monitorado a uma conexão ADO."""
    repo = ConfigRepository(db)
    # TODO: Adicionar validação se o user_id é dono da connection_id
    proj = repo.create_ado_project(project_in.connection_id, project_in.project_name)
    return proj

@router.get("/projects/{connection_id}", response_model=List[AdoProject])
async def get_ado_projects(
    connection_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Lista os projetos monitorados de uma conexão ADO específica."""
    repo = ConfigRepository(db)
    # TODO: Adicionar validação se o user_id é dono da connection_id
    return repo.get_ado_projects_for_connection(connection_id)


@router.post("/connections/{connection_id}/refresh-projects", response_model=List[AdoProject])
async def refresh_ado_projects(
    connection_id: int,
    user_id: int = Depends(get_current_user_id),
    ado_token: str = Depends(get_ado_token),
    db: Session = Depends(get_db)
):
    """Força a atualização da lista de projetos a partir da organização ADO configurada."""
    repo = ConfigRepository(db)
    conn = repo.get_ado_connection_by_id(connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Conexão ADO não encontrada.")
    if conn.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta conexão.")

    try:
        updated = await repo.sync_ado_projects_for_connection(connection_id, conn.organization_url, ado_token)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao sincronizar projetos: {e}")