# backend/api/config.py (ATUALIZADO COM CACHE DE 1 HORA)

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from cachetools import cached, TTLCache # NOVO: Importa a ferramenta de cache

# Cache para configuração: 1 hora de validade (3600 segundos)
CONFIG_CACHE = TTLCache(maxsize=10, ttl=3600) 

# Função auxiliar para gerar a chave de cache baseada no user_id (para o endpoint de usuário)
def user_config_cache_key(user_id: int) -> int:
    return user_id

# --- Modelos Pydantic (Não Alterados) ---
class SystemModuleDetail(BaseModel):
    id: str
    name: str
    description: str
    api_endpoint: str
    grid_column_span: int

class UserModulePreference(BaseModel):
    module_id: str
    user_id: int
    is_active: bool
    display_order: int

class UserConfig(BaseModel):
    user_id: int
    theme: str
    modules: List[UserModulePreference]

# --- Dados Mockados (Não Alterados) ---
SYSTEM_MODULES: List[SystemModuleDetail] = [
    SystemModuleDetail(
        id="context_agent",
        name="Contexto e Foco",
        description="Agrega comunicações e define o foco de trabalho atual.",
        api_endpoint="/contexto/agregado",
        grid_column_span=2
    ),
    SystemModuleDetail(
        id="skill_agent",
        name="Sugestão de Skills",
        description="Sugere habilidades de aprendizado com base no foco crítico.",
        api_endpoint="/skill/sugestoes",
        grid_column_span=1
    ),
    SystemModuleDetail(
        id="reserve_agent",
        name="Reserva de Recursos",
        description="Sugere a reserva de salas de foco para momentos críticos.",
        api_endpoint="/reserva/sugestao",
        grid_column_span=1
    ),
    SystemModuleDetail(
        id="project_health",
        name="Saúde do Projeto",
        description="Monitora a saúde geral de projetos (Atualmente inativo).",
        api_endpoint="/projeto/saude",
        grid_column_span=2
    ),
]

USER_PREFERENCES: Dict[int, UserConfig] = {
    42: UserConfig(
        user_id=42,
        theme="dark",
        modules=[
            UserModulePreference(
                module_id="context_agent",
                user_id=42,
                is_active=True,
                display_order=1
            ),
            UserModulePreference(
                module_id="skill_agent",
                user_id=42,
                is_active=True,
                display_order=2
            ),
            UserModulePreference(
                module_id="reserve_agent",
                user_id=42,
                is_active=True,
                display_order=3
            ),
            UserModulePreference(
                module_id="project_health",
                user_id=42,
                is_active=False,
                display_order=99
            ),
        ]
    )
}

# --- Rotas da API ---
router = APIRouter()

@router.get("/system/modules", response_model=List[SystemModuleDetail])
@cached(CONFIG_CACHE) # 👈 Cache aplicado!
def get_system_modules_config():
    """Retorna os detalhes de todos os módulos disponíveis no sistema."""
    return SYSTEM_MODULES

@router.get("/user/{user_id}", response_model=UserConfig)
@cached(CONFIG_CACHE, key=user_config_cache_key) # 👈 Cache aplicado!
def get_user_config(user_id: int):
    """Retorna as preferências de dashboard de um usuário específico."""
    if user_id not in USER_PREFERENCES:
        return USER_PREFERENCES[42] 
    return USER_PREFERENCES[user_id]