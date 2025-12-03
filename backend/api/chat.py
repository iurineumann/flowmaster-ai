# backend/api/chat.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from ..utils.security import get_current_user_id, get_graph_token
from ..services.context_data_service import get_context_data_service, ContextDataService
# Importa do knowledge module corrigido
from ..knowledge_module import analyze_context_with_llm 

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
    access_token: str = Depends(get_graph_token),
    context_service: ContextDataService = Depends(get_context_data_service)
):
    try:
        # Tenta buscar contexto
        # Se get_all_raw_context não existir no service, usamos um fallback vazio
        try:
            all_raw_data = await context_service.get_aggregated_context(user_id)
            # Adaptação simples se retornar dict
            context_str = str(all_raw_data)
        except:
            context_str = ""

        # Chama a LLM através do Facade
        llm_result = await analyze_context_with_llm(request.message, context={"raw": context_str})
        
        return ChatResponse(
            response=getattr(llm_result, "summary_analysis", "Sem resposta."),
            context_used=["Contexto dinâmico"]
        )

    except Exception as e:
        print(f"Erro no Chat: {e}")
        return ChatResponse(response="Erro ao processar mensagem.", context_used=[])