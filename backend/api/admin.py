# backend/api/admin.py (MÓDULO DE ADMINISTRAÇÃO ATUALIZADO)

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
import os

from ..utils.security import get_current_user_id
from ..db.database import get_db
from ..services.config_repository import ConfigRepository
from ..utils.multi_layer_cache import get_cache_stats
from ..utils.ws_manager import manager # Importa a instância real

router = APIRouter()

class SystemStats(BaseModel):
    total_llm_calls: int
    cache_hits: int
    cache_misses: int
    cache_efficiency: str
    active_ws_connections: int
    registered_users: int

# Endpoint para Estatísticas de Performance e Custo
@router.get("/stats", response_model=SystemStats, tags=["Administração"], status_code=status.HTTP_200_OK)
async def get_system_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas vitais para controle de custos e performance (LLM, Cache, Usuários).
    """
    repo = ConfigRepository(db)
    
    # 1. Busca Estatísticas Reais do Cache (Redis)
    cache_stats = await get_cache_stats()
    
    total_hits = cache_stats["hits_l1"] + cache_stats["hits_l2"]
    total_misses = cache_stats["misses"]
    total_llm_calls = cache_stats["llm_calls"]
    
    total_cache_ops = total_hits + total_misses
    efficiency = (total_hits / total_cache_ops) * 100 if total_cache_ops > 0 else 0
    
    # 2. Busca Estatísticas Reais do Usuário/DB
    registered_users = repo.count_all_users() 

    # 3. Busca Estatísticas Reais do WebSocket
    active_ws = manager.get_active_connections_count()

    return SystemStats(
        total_llm_calls=total_llm_calls,
        cache_hits=total_hits,
        cache_misses=total_misses,
        cache_efficiency=f"{efficiency:.1f}%",
        active_ws_connections=active_ws,
        registered_users=registered_users
    )