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
        # 1. Contexto do Usuário (Tarefas, Cargo)
        user_context = await context_service.get_aggregated_context(user_id)
        
        # 2. Contexto RAG (Documentos)
        docs = await find_relevant_document(request.message)
        
        # 3. Prompt Enriquecido
        rag_context = {
            "user_profile": user_context,
            "retrieved_documents": docs
        }
        
        # 4. Geração
        llm_result = await analyze_context_with_llm(request.message, context=rag_context)
        
        sources = [d['title'] for d in docs]
        if user_context.get('active_tasks'):
            sources.append("Suas Tarefas (ADO)")

        return ChatResponse(
            response=getattr(llm_result, "summary_analysis", "Não entendi."),
            context_used=sources
        )

    except Exception as e:
        print(f"Erro chat: {e}")
        return ChatResponse(
            response="Desculpe, não consegui processar sua solicitação no momento.",
            context_used=[]
        )