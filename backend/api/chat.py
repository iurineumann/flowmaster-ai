# backend/api/chat.py (CORRIGIDO O IMPORT)

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from ..utils.security import get_current_user_id, get_access_token_mock # ✅ CORREÇÃO AQUI
from ..services.graph_repository import GraphRepository 
from ..services.llm_service import analyze_context_with_llm_real 

router = APIRouter()

class ChatRequest(BaseModel):
# ... (O corpo da classe ChatRequest permanece o mesmo)
    message: str
    
class ChatResponse(BaseModel):
# ... (O corpo da classe ChatResponse permanece o mesmo)
    response: str
    context_used: List[str]

@router.post("/query", response_model=ChatResponse)
async def chat_with_context(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token_mock)
):
    """
    Permite ao usuário interagir com a LLM sobre seu contexto de trabalho.
    """
    repo = GraphRepository()
    all_raw_data = await repo.get_raw_context_by_user(user_id, access_token)
    
    # Simulação: Agrega o contexto relevante (poderia usar o K-Search aqui)
    relevant_context = [
        item.content_preview 
        for item in all_raw_data 
        if item.project_tag == "CLIENTE_X"
    ]
    
    # 🧠 Simulação de Prompt de Chat (Em produção, usaria o LLM Service com um novo prompt)
    combined_context = "\n---\n".join(relevant_context)
    
    if not relevant_context:
        return ChatResponse(
            response="Não encontrei contexto relevante para esta conversa. Tente uma pergunta mais geral.",
            context_used=[]
        )

    # Nota: Reutilizamos a função de LLM, mas para uma tarefa de chat. 
    # Em um sistema real, haveria um prompt e uma função de LLM dedicada para Chat.
    
    # Simula a resposta da LLM
    simulated_llm_response = f"Com base nas comunicações recentes sobre 'CLIENTE_X', a falha de pagamento requer a atenção da Elena. Sua pergunta: '{request.message}' foi analisada à luz do BUG CRÍTICO, que é o seu foco atual."
    
    return ChatResponse(
        response=simulated_llm_response,
        context_used=relevant_context
    )