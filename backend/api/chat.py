# backend/api/chat.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from ..utils.security import get_current_user_id, get_access_token_mock
from ..services.context_data_service import ContextDataService, get_context_data_service
from ..services.llm_service import analyze_context_with_llm_real 

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    context_used: List[str]

@router.post("/query", response_model=ChatResponse)
async def chat_with_context(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    all_raw_data = await context_service.get_all_raw_context(user_id, access_token)
    
    relevant_context = [
        item.content_preview 
        for item in all_raw_data 
        if item.project_tag == context_service.foco_critico_tag # Usa tag do serviço
    ]
    
    combined_context = "\n---\n".join(relevant_context)
    
    if not relevant_context:
        return ChatResponse(
            response="Não encontrei contexto relevante para esta conversa. Tente uma pergunta mais geral.",
            context_used=[]
        )

    # Simulação de Prompt de Chat (RAG Leve)
    simulated_llm_response = f"""
    Com base nas comunicações recentes (Foco: '{context_service.foco_critico_tag}'),
    a análise indica que a falha de pagamento requer a atenção imediata.
    Sua pergunta: '{request.message}' foi analisada à luz do CONTEXTO CRÍTICO.
    A ação imediata recomendada é: Consultar o guia de migração Cripto V3.
    """
    
    return ChatResponse(
        response=simulated_llm_response.strip(),
        context_used=[item.subject_or_title for item in all_raw_data if item.project_tag == context_service.foco_critico_tag]
    )