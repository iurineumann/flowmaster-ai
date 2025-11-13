# backend/api/admin.py (NOVO MÓDULO DE ADMINISTRAÇÃO)

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from ..utils.security import get_current_user_id
from ..db.database import get_db
from ..services.config_repository import ConfigRepository
from ..utils.multi_layer_cache import get_cache_stats # Assume que esta função existe

router = APIRouter()

class SystemStats(BaseModel):
    total_llm_calls: int
    cache_hits: int
    cache_misses: int
    cache_efficiency: str
    active_ws_connections: int
    registered_users: int

# Endpoint para Estatísticas de Performance e Custo
# Este endpoint DEVE ser protegido por um escopo de permissão 'admin' em produção!
@router.get("/stats", response_model=SystemStats, tags=["Administração"], status_code=status.HTTP_200_OK)
async def get_system_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas vitais para controle de custos e performance (LLM, Cache, Usuários).
    """
    # 🚨 NOTA: Em produção, adicione uma verificação de permissão:
    # if not ConfigRepository(db).user_has_admin_role(user_id):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    
    repo = ConfigRepository(db)
    
    # 1. Estatísticas de Cache (simuladas se a função real não existir)
    cache_stats = get_cache_stats() if 'get_cache_stats' in globals() else {
        "hits": 450, "misses": 50
    }
    
    total_cache_ops = cache_stats["hits"] + cache_stats["misses"]
    efficiency = (cache_stats["hits"] / total_cache_ops) * 100 if total_cache_ops > 0 else 0
    
    # 2. Estatísticas de Usuário/DB
    registered_users = repo.count_all_users() # Presume a existência da função no ConfigRepository
    
    # 3. Estatísticas LLM (Mock de Custo)
    total_llm_calls = int(os.environ.get("MOCK_LLM_CALLS", "100")) # Usar um contador real em produção!

    # 4. Estatísticas WebSocket (mock)
    from ..utils.ws_manager import manager
    active_ws = manager.get_active_connections_count()

    return SystemStats(
        total_llm_calls=total_llm_calls,
        cache_hits=cache_stats["hits"],
        cache_misses=cache_stats["misses"],
        cache_efficiency=f"{efficiency:.1f}%",
        active_ws_connections=active_ws,
        registered_users=registered_users
    )