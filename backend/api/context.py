# backend/api/context.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..utils.security import get_current_user
from ..db.models import UserModel
from ..services.ado_repository import AdoRepository

router = APIRouter()

class ContextoAgregadoResponse(BaseModel):
    usuario: str
    funcao: str
    projeto_atual: str
    sprint_atual: str
    tarefas_pendentes: int
    proxima_reuniao: Optional[str] = None
    alertas: List[str] = []

@router.get("/agregado", response_model=ContextoAgregadoResponse)
async def get_contexto_agregado(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    nome_usuario = user.full_name or user.email
    tarefas_count = 0
    projeto = "Nenhum projeto ativo"
    
    try:
        # Tenta inicializar sem token ou recuperando token OBO se disponível no banco
        # Em produção real, desencriptaríamos o user.entra_refresh_token aqui
        ado_repo = AdoRepository(db, access_token=None)
        
        # Como estamos sem token direto aqui (exceto se implementarmos a troca OBO completa agora)
        # O repositório retornará vazio graciosamente em vez de quebrar
        work_items = await ado_repo.get_work_items_for_user(user.id)
        if work_items:
            tarefas_count = len(work_items)
            projeto = work_items[0].project
            
    except Exception as e:
        print(f"Aviso de contexto: {e}")

    return ContextoAgregadoResponse(
        usuario=nome_usuario,
        funcao="Membro FlowMaster",
        projeto_atual=projeto,
        sprint_atual="Sprint Atual",
        tarefas_pendentes=tarefas_count,
        proxima_reuniao=None,
        alertas=[]
    )