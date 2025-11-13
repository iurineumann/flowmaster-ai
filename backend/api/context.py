# backend/api/context.py (CORREÇÃO FINAL DE IMPORTAÇÃO E CACHE MULTI-CAMADAS)

from fastapi import APIRouter, Depends 
from typing import Dict, Any, Callable
import os 
# ✅ NOVO: Importa o cache multi-camadas customizado
from ..utils.multi_layer_cache import multi_layer_cache 

# IMPORTS
# ✅ CORREÇÃO CRÍTICA: Mudar para get_real_access_token
from ..services.graph_repository import get_real_access_token, GraphRepository 
from ..knowledge_module import find_relevant_document, analyze_context_with_llm
from ..utils.security import get_current_user_id 
from ..utils.event_dispatcher import dispatch_event, CriticalContextDetectedEvent
from ..utils.ws_manager import manager 

# --- Configuração de Cache - AGORA USANDO CACHE MULTI-CAMADAS (REDIS + MEMÓRIA) ---

# Define a função de construção da chave de cache a partir dos argumentos
# A chave deve ser única por usuário.
def cache_key_for_user_context_agregado(
    user_id: int, 
    access_token: str
) -> str:
    """Usa o user_id como chave de cache principal."""
    # Retorna uma string que será a chave no Redis e Memória.
    return f"user_context_agregado_id:{user_id}"

repo = GraphRepository()
router = APIRouter()

@router.get("/agregado", response_model=Dict[str, Any])
@multi_layer_cache(
    ttl=60,      # TTL no Redis (Layer 2) - 1 minuto
    memory_ttl=10, # TTL na Memória (Layer 1) - 10 segundos
    key_builder=cache_key_for_user_context_agregado
)
async def get_user_context_agregado(
    user_id: int = Depends(get_current_user_id),
    # ✅ CORREÇÃO CRÍTICA: Mudar para o Dependência de Token REAL
    access_token: str = Depends(get_real_access_token) 
):
    """
    Endpoint principal que agrega contexto, agora notifica via WS em caso de crise.
    """
    
    all_raw_data = await repo.get_raw_context_by_user(user_id, access_token)
    
    foco_critico_tag = "CLIENTE_X"
    itens_do_foco = [item for item in all_raw_data if item.project_tag == foco_critico_tag]
    
    if not itens_do_foco:
        # Fallback se não houver dados críticos
        return {
            "user_id": user_id,
            "foco_critico": foco_critico_tag,
            "summary_data": None,
            "urgencia": 0,
            "sugestoes_conhecimento": []
        }

    problema_detalhado = itens_do_foco[0].content_preview 

    # 2. Chamada ao Serviço de LLM Otimizado (assíncrona)
    summary_data = await analyze_context_with_llm(problema_detalhado) 
    
    # 3. Disparo de Evento (Geral)
    critical_event = CriticalContextDetectedEvent(
        payload={
            "user_id": user_id,
            "project": foco_critico_tag,
            "detail": summary_data.summary_analysis
        }
    )
    dispatch_event(critical_event)
    
    # 4. Notificação em Tempo Real (WebSockets)
    if summary_data.urgency_score >= 90:
        notification_message = {
            "type": "CRITICAL_BUG_ALERT",
            "title": summary_data.focus_title,
            "urgency": summary_data.urgency_score,
            "detail": summary_data.summary_analysis
        }
        # Envia a notificação via WebSocket
        await manager.send_personal_message(notification_message, user_id)
    
    # 5. K-Search (chamada assíncrona)
    sugestoes_conhecimento = await find_relevant_document( 
        query_text=problema_detalhado, 
        top_k=2
    )
    
    # 6. Retorno da API
    return {
        "user_id": user_id,
        "foco_critico": foco_critico_tag,
        "summary_data": summary_data.model_dump(), # Usa model_dump() do Pydantic V2
        "urgencia": summary_data.urgency_score,
        "sugestoes_conhecimento": sugestoes_conhecimento
    }