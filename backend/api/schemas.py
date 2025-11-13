# backend/api/schemas.py

from pydantic import BaseModel
from typing import List

# --- Modelos Pydantic para a Resposta da API ---

class SystemModuleDetail(BaseModel):
    """Detalhes de um módulo do sistema (global)."""
    id: str
    name: str
    description: str
    api_endpoint: str 
    grid_column_span: int
    
    class Config:
        # Permite que o Pydantic leia de um modelo SQLAlchemy (ORM Mode)
        from_attributes = True

class UserModulePreference(BaseModel):
    """Preferências do usuário para um módulo específico."""
    module_id: str
    is_active: bool
    display_order: int

class UserConfig(BaseModel):
    """Configuração completa do usuário."""
    user_id: int
    theme: str
    modules: List[UserModulePreference]
    
    class Config:
        from_attributes = True

# Schema de resposta para o token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
