# backend/api/ado_config.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
from ..utils.security import get_current_user_id, encrypt_token
from ..services.config_repository import ConfigRepository
from .schemas import AdoConnectionCreate, AdoConnectionResponse, AdoConnectionUpdate # Importe os schemas atualizados

router = APIRouter()

@router.get("/connections", response_model=List[AdoConnectionResponse])
def get_connections(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = ConfigRepository(db)
    conns = repo.get_ado_connections(user_id)
    
    # Mapeia para resposta indicando se tem PAT, sem revelar o token
    return [
        AdoConnectionResponse(
            id=c.id,
            organization_url=c.organization_url,
            is_active=c.is_active,
            has_pat=bool(c.personal_access_token)
        ) for c in conns
    ]

@router.post("/connections", response_model=AdoConnectionResponse)
def create_connection(
    config: AdoConnectionCreate, 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    repo = ConfigRepository(db)
    try:
        # Criptografa o PAT se fornecido
        encrypted_pat = None
        if config.personal_access_token:
            encrypted_pat = encrypt_token(config.personal_access_token)

        new_conn = repo.add_ado_connection(
            user_id, 
            config.organization_url,
            personal_access_token=encrypted_pat # Passa o PAT criptografado
        )
        
        return AdoConnectionResponse(
            id=new_conn.id,
            organization_url=new_conn.organization_url,
            is_active=new_conn.is_active,
            has_pat=bool(new_conn.personal_access_token)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection(
    connection_id: int, 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    repo = ConfigRepository(db)
    success = repo.delete_ado_connection(user_id, connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
    return None

# ✅ NOVO: Endpoint PATCH (Atualizar PAT)
@router.patch("/connections/{connection_id}", response_model=AdoConnectionResponse)
def update_connection_pat(
    connection_id: int, 
    config: AdoConnectionUpdate, 
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    repo = ConfigRepository(db)
    # Criptografa o novo token antes de salvar
    encrypted_pat = encrypt_token(config.personal_access_token)
    
    updated_conn = repo.update_ado_connection_pat(user_id, connection_id, encrypted_pat)
    
    if not updated_conn:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
        
    return AdoConnectionResponse(
        id=updated_conn.id,
        organization_url=updated_conn.organization_url,
        is_active=updated_conn.is_active,
        has_pat=True
    )