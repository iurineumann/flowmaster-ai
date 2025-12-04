# backend/api/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

# --- Modelos Pydantic para a Resposta da API ---

class SystemModuleDetail(BaseModel):
    id: str
    name: str
    description: str
    api_endpoint: str 
    grid_column_span: int
    
    class Config:
        from_attributes = True

class UserModulePreference(BaseModel):
    module_id: str
    is_active: bool
    display_order: int

class UserConfig(BaseModel):
    user_id: int
    theme: str
    modules: List[UserModulePreference]
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int

# --- NOVOS SCHEMAS (ADO Config) ---

class AdoConnectionBase(BaseModel):
    organization_url: str = Field(..., example="https://dev.azure.com/MinhaOrganizacao")

class AdoConnectionCreate(BaseModel):
    organization_url: str
    # ✅ Opcional: O usuário pode fornecer o PAT na criação
    personal_access_token: Optional[str] = None
    
class AdoConnectionUpdate(BaseModel):
    personal_access_token: str

class AdoConnectionResponse(BaseModel):
    id: int
    organization_url: str
    is_active: bool
    has_pat: bool = False 

    class Config:
        from_attributes = True

class AdoConnection(AdoConnectionBase):
    id: int
    user_id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class AdoProjectBase(BaseModel):
    project_name: str = Field(..., example="MeuProjeto")

class AdoProjectCreate(AdoProjectBase):
    connection_id: int # O ID da Organização/Conexão

class AdoProject(AdoProjectBase):
    id: int
    connection_id: int
    is_active: bool

    class Config:
        from_attributes = True