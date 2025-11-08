# backend/api/reserve.py
from fastapi import APIRouter
from backend.reserve_mock import RESERVE_MOCK_DATABASE, FOCUS_TO_RESERVE_MOCK, ReserveSuggestion

router = APIRouter()

@router.get("/suggestion/{project_tag}", response_model=ReserveSuggestion)
def get_reserve_suggestion(project_tag: str):
    """
    Simula o endpoint de Reserva Inteligente que sugere um recurso (mesa, sala) 
    baseado no tag do projeto (contexto).
    """
    tag_upper = project_tag.upper()
    
    # 1. Mapeia a tag do projeto para a regra de reserva (e.g., 'SECURITY_IAM')
    rule_key = FOCUS_TO_RESERVE_MOCK.get(tag_upper)
    
    # 2. Busca a sugestão de recurso correspondente
    suggestion = RESERVE_MOCK_DATABASE.get(rule_key)
    
    if not suggestion:
        # Sugestão padrão se o foco não for encontrado no mock
        return ReserveSuggestion(
            resource_id="DEF01",
            resource_type="desk",
            suggested_location="Mesa Padrão Disponível (DEF01)",
            reason="Nenhuma necessidade de co-location crítica detectada. Reserva automática no seu setor."
        )
        
    return suggestion