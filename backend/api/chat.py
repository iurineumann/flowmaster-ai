# backend/api/chat.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from ..utils.security import get_current_user_id
from ..services.graph_repository import get_real_access_token
from ..services.context_data_service import ContextDataService, get_context_data_service
from ..knowledge_module import analyze_context_with_llm # Importa o facade da LLM

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
    access_token: str = Depends(get_real_access_token),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    all_raw_data = await context_service.get_all_raw_context(user_id, access_token)
    
    relevant_context = [
        item.content_preview 
        for item in all_raw_data 
        if item.project_tag == context_service.foco_critico_tag
    ]
    
    combined_context = "\n---\n".join(relevant_context)
    
    # ✅ CORREÇÃO DA LÓGICA DE CHAT
    if not relevant_context:
        print("ℹ️ [Chat] Nenhum contexto de trabalho encontrado. Usando modo de Chat Geral.")
        # Se não há contexto, envia a própria pergunta do usuário para a LLM
        # (O 'analyze_context_with_llm' irá "resumir" a pergunta, o que funciona como uma resposta simples)
        summary_data = await analyze_context_with_llm(request.message)
        
        if not summary_data:
             return ChatResponse(response="Serviço de IA indisponível no momento.", context_used=[])

        return ChatResponse(
            response=summary_data.summary_analysis, # Retorna a análise da LLM sobre a pergunta
            context_used=["Nenhum contexto de trabalho foi usado."]
        )

    # Fluxo normal (com contexto)
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