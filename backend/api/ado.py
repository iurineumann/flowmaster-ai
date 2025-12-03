# backend/api/ado.py (NOVO AGENTE ADO)

import os
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from aiocache import cached
from aiocache.backends.redis import RedisCache
from sqlalchemy.orm import Session

# ✅ CORREÇÃO: get_current_user_id é necessário para o cache_key_builder
from ..utils.security import get_current_user_id, get_ado_token
from ..db.database import get_db
from ..services.ado_repository import AdoRepository, AdoWorkItem

# --- Configuração de Cache (Padronizado) ---
CACHE_KWARGS = {
    'cache': RedisCache,
    'endpoint': os.environ.get('REDIS_ENDPOINT', "redis"),
    'port': 6379,
    'ttl': 300 # Cache de 5 minutos para Work Items
}

def cache_key_builder(func, *args, **kwargs):
    user_id = kwargs.get('user_id')
    return f"ado_work_items:{user_id}"

router = APIRouter()

@router.get("/work_items", response_model=List[AdoWorkItem])
@cached(
    key_builder=cache_key_builder,
    **CACHE_KWARGS
)
async def get_user_work_items(
    user_id: int = Depends(get_current_user_id), # Necessário para o key_builder
    ado_token: str = Depends(get_ado_token), # Token delegado (OBO)
    db: Session = Depends(get_db)
):
    """
    Endpoint do Agente ADO. 
    Busca todos os work items (Bugs, Tasks) atribuídos ao usuário
    em todas as organizações e projetos configurados.
    """
    repo = AdoRepository(db=db, access_token=ado_token)
    work_items = await repo.get_work_items_for_user(user_id)
    return work_items