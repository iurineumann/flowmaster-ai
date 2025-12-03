# backend/api/chat.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from ..utils.security import get_current_user_id
from ..services.context_data_service import get_context_data_service, ContextDataService
from ..knowledge_module import find_relevant_document, analyze_context_with_llm

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
    context_service: ContextDataService = Depends(get_context_data_service)
):
    try:
        # 1. Recuperar Contexto do Usuário (Perfil, Tasks)
        user_context = await context_service.get_aggregated_context(user_id)
        
        # 2. Recuperar Contexto da Base de Conhecimento (RAG)
        # Busca documentos relevantes à mensagem do usuário
        rag_docs = await find_relevant_document(request.message)
        
        # 3. Enriquecer Contexto para a LLM
        full_context = {
            "user_profile": user_context,
            "knowledge_base": rag_docs
        }
        
        # 4. Gerar Resposta
        llm_result = await analyze_context_with_llm(request.message, context=full_context)
        
        # Extrai títulos dos documentos usados para referência
        sources = [d['title'] for d in rag_docs] if rag_docs else ["Conhecimento Geral"]

        return ChatResponse(
            response=getattr(llm_result, "summary_analysis", "Não entendi."),
            context_used=sources
        )

    except Exception as e:
        print(f"Erro no Chat API: {e}")
        return ChatResponse(response="Desculpe, encontrei um erro interno.", context_used=[])