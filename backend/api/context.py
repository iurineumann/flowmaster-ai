# backend/api/context.py (CORRIGIDO COM IMPORTS RELATIVOS)
from fastapi import APIRouter
from typing import Dict, Any

# IMPORTS CORRIGIDOS: Usando '..' para subir um nível e acessar os módulos vizinhos
from ..graph_mock import MOCK_RAW_DATA
from ..knowledge_module import find_relevant_document

router = APIRouter()

@router.get("/agregado/{user_id}", response_model=Dict[str, Any])
def get_user_context_agregado(user_id: int):
    """
    Endpoint principal que agrega contexto e executa o K-Search.
    """
    
    # Lógica de Foco Crítico (Mantida)
    foco_critico_tag = "CLIENTE_X"
    itens_do_foco = [item for item in MOCK_RAW_DATA if item.project_tag == foco_critico_tag]
    
    if not itens_do_foco:
        # Retorna contexto vazio se não houver dados mockados
        return {
            "user_id": user_id,
            "foco_atual_titulo": "Nenhum Foco Imediato Detectado",
            "resumo_ia": "Aguardando dados de comunicação para análise.",
            "numero_itens_agregados": 0,
            "proxima_reuniao": "Nenhuma agendada.",
            "sugestoes_conhecimento": []
        }

    problema_detalhado = itens_do_foco[0].content_preview 

    # IA de Busca de Conhecimento (K-Search)
    sugestoes_conhecimento = find_relevant_document(
        query_text=problema_detalhado, 
        top_k=2
    )
    
    # Resumo e Próxima Reunião
    descricao_resumo = f"Requer atenção imediata: {len(itens_do_foco)} comunicações recentes. O problema detalhado é: '{problema_detalhado[:70]}...'"
    proxima_reuniao = "Daily Standup (Projeto Y)" 

    return {
        "user_id": user_id,
        "foco_atual_titulo": f"Foco Imediato: {foco_critico_tag}",
        "resumo_ia": descricao_resumo,
        "numero_itens_agregados": len(itens_do_foco),
        "proxima_reuniao": proxima_reuniao,
        "sugestoes_conhecimento": sugestoes_conhecimento
    }