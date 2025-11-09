# backend/api/context.py (AGORA IMPLEMENTA O RAG REAL NO K-SEARCH)
from fastapi import APIRouter
from typing import Dict, Any, List

from ..knowledge_module import find_relevant_document, SugestaoConhecimento
from ..context_agent import ContextAgent 
from ..llm_connector import llm_connector # NOVO: Importa o conector para a chamada RAG

router = APIRouter()

@router.get("/agregado/{user_id}", response_model=Dict[str, Any])
def get_user_context_agregado(user_id: int):
    """
    Endpoint principal que usa o Agente de Contexto e implementa o RAG real para o K-Search.
    """
    
    # 1. Executa o Agente de Contexto para obter o Foco e Resumo (LLM On-Premise)
    context_agent = ContextAgent(user_id=user_id)
    contexto_agregado = context_agent.get_aggregated_context(project_tag="CLIENTE_X")
    
    if contexto_agregado["numero_itens_agregados"] == 0:
        return contexto_agregado 

    # 2. Prepara a Query (o resumo do LLM é a melhor query)
    itens_brutos = contexto_agregado.pop("raw_items")
    # Usamos o Foco Crítico Gerado pelo LLM como a QUERY de busca (melhor que o texto bruto)
    foco_critico_query = contexto_agregado["resumo_ia"]

    # 3. Executa a IA de Busca de Conhecimento (K-Search)
    # Retorna uma lista de objetos SugestaoConhecimento com o full_content preenchido.
    sugestoes_iniciais: List[SugestaoConhecimento] = find_relevant_document(
        query_text=foco_critico_query, 
        top_k=2
    )
    
    sugestoes_finais = []
    # 4. Loop RAG: Para cada documento, chamamos o LLM para resumir o seu conteúdo.
    for sugestao in sugestoes_iniciais:
        # Chamada REAL RAG: O LLM On-Premise resume o 'full_content'
        resumo_gerado_pelo_llm = llm_connector.generate_rag_summary(
            document_content=sugestao.full_content,
            focus_query=foco_critico_query
        )
        
        # Preenche o campo que o Frontend consome com o resumo REAL
        sugestao.content_preview = resumo_gerado_pelo_llm
        sugestoes_finais.append(sugestao)
    
    # 5. Monta a Resposta Final
    contexto_agregado["sugestoes_conhecimento"] = sugestoes_finais
    
    return contexto_agregado