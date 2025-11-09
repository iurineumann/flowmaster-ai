# backend/initial_data_mock.py (Dados para Migração Inicial do PostgreSQL)
from pydantic import BaseModel
from typing import Dict, List, Optional

# --- Modelos Pydantic Simples para Estrutura do Mock ---
class ModuleConfig(BaseModel):
    id: str
    name: str
    is_available: bool = True
    description: str
    llm_model_name: str = "mistral:7b-instruct-q4_K_M"
    llm_prompt_template: str
    api_endpoint: str
    api_key_system: Optional[str] = None
    display_order: int

class UserModulePreference(BaseModel):
    module_id: str
    is_active: bool = True
    display_order: int
    consent_given: bool = True

class UserConfig(BaseModel):
    user_id: int
    modules: List[UserModulePreference]
    theme: str = "dark"

# --- Dados MOCK de Configuração de Sistema ---
SYSTEM_MODULES_CONFIG: Dict[str, ModuleConfig] = {
    "context_agent": ModuleConfig(
        id="context_agent", name="Foco Crítico e Contexto", description="...",
        llm_prompt_template="Analise os itens e extraia o foco crítico e a solução. Contexto Bruto: {raw_data}",
        api_endpoint="/contexto/agregado", api_key_system="MOCK_MS_GRAPH_KEY_v2", display_order=1
    ),
    "skill_agent": ModuleConfig(
        id="skill_agent", name="Skill-Boost & Mentoria", description="...",
        llm_prompt_template="Analise o foco do usuário ({focus}) e sugira o melhor curso ou mentor.",
        api_endpoint="/skill/suggestions", display_order=2
    ),
    "reserve_agent": ModuleConfig(
        id="reserve_agent", name="Reserva Inteligente", description="...",
        llm_prompt_template="Com o foco ({focus}) e agenda ({calendar}), qual recurso físico é o ideal?",
        api_endpoint="/reserva/suggestion", display_order=3
    ),
}

# --- Dados MOCK de Configuração de Usuário ---
USER_CONFIG_MOCK_DATABASE: Dict[int, UserConfig] = {
    42: UserConfig(
        user_id=42,
        modules=[
            UserModulePreference(module_id="context_agent", is_active=True, display_order=10),
            UserModulePreference(module_id="skill_agent", is_active=True, display_order=20),
            UserModulePreference(module_id="reserve_agent", is_active=True, display_order=30),
        ]
    )
}