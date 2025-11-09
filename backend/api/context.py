# backend/api/context.py (FINAL - COM DATA MASKING INTEGRADO)
from fastapi import APIRouter
from typing import Dict, Any, List
from cachetools import cached, TTLCache

# Imports dos Agentes
from ..graph_mock import MOCK_RAW_DATA
from ..knowledge_module import find_relevant_document
from ..context_agent import ContextAgent 
from ..llm_connector import llm_connector 
from ..data_security import process_and_mask_raw_data # NOVO: Importa o serviço de segurança

router = APIRouter()

# Cache de 60 segundos para dados que mudam com frequência
AGENT_DATA_CACHE = TTLCache(maxsize=128, ttl=60) 

def agent_cache_key(user_id: int) -> int:
    """Função para chavear o cache por usuário."""
    return user_id

@router.get("/agregado/{user_id}", response_model=Dict[str, Any])
@cached(AGENT_DATA_CACHE, key=agent_cache_key)
def get_user_context_agregado(user_id: int):
    """
    Endpoint principal que agrega contexto, aplica data masking e executa o K-Search.
    """
    
    # 1. Simulação da Recuperação dos Dados Brutos (Antes do Mascaramento)
    foco_critico_tag = "CLIENTE_X"
    itens_brutos = [item for item in MOCK_RAW_DATA if item.project_tag == foco_critico_tag]
    
    if not itens_brutos:
        # ... (retorna contexto vazio se não houver dados mockados) ...
        # (Lógica mantida para retornar contexto vazio se não houver dados)
        return {
            "user_id": user_id,
            "foco_atual_titulo": "Nenhum Foco Imediato Detectado",
            "resumo_ia": "Aguardando dados de comunicação para análise.",
            "numero_itens_agregados": 0,
            "proxima_reuniao": "Nenhuma agendada.",
            "sugestoes_conhecimento": []
        }

    # 2. PASSO DE SEGURANÇA CRÍTICO: DATA MASKING (DIL)
    # Aplica o mascaramento em todos os itens de contexto
    itens_mascarados = process_and_mask_raw_data(itens_brutos)
    
    # 3. Executa o Agente de Contexto (AGORA COM DADOS SEGUROS)
    # O Agente de Contexto agora recebe a lista de RawContextItem mascarados
    context_agent = ContextAgent(user_id=user_id)
    # A chamada deve usar os itens mascarados (ou um resumo pré-processado deles)
    
    # Simplificando a chamada para usar o novo modelo (com ContextAgent)
    # NOTE: O ContextAgent precisa ser adaptado para receber a lista mascarada, 
    # mas o mock atual apenas usa o primeiro item como "problema_detalhado"
    
    # Para manter a compatibilidade com o mock anterior, vamos usar o item mascarado
    # para a chamada do LLM, que é o que realmente precisa da segurança.
    
    # Gerando o resumo LLM com dados mascarados (melhorando o ContextAgent)
    resumo_ia_gerado = llm_connector.analyze_and_summarize_context(
        items=itens_mascarados,
        user_name=f"Usuário {user_id}"
    )

    # 4. Continuação da Lógica do K-Search (RAG)
    foco_critico_query = resumo_ia_gerado
    sugestoes_iniciais: List[SugestaoConhecimento] = find_relevant_document(
        query_text=foco_critico_query, 
        top_k=2
    )
    
    sugestoes_finais = []
    for sugestao in sugestoes_iniciais:
        resumo_gerado_pelo_llm = llm_connector.generate_rag_summary(
            document_content=sugestao.full_content, # O conteúdo do documento de conhecimento NÃO precisa de mascaramento
            focus_query=foco_critico_query
        )
        sugestao.content_preview = resumo_gerado_pelo_llm
        sugestoes_finais.append(sugestao)
    
    # 5. Monta a Resposta Final
    contexto_agregado = {
        "user_id": user_id,
        "foco_atual_titulo": f"Foco Crítico: {itens_brutos[0].subject_or_title}",
        "resumo_ia": resumo_ia_gerado,
        "numero_itens_agregados": len(itens_brutos),
        "proxima_reuniao": "14:00 - Reunião de Crise (Alocada)",
        "sugestoes_conhecimento": sugestoes_finais,
        "raw_items_example_masked": [item.dict() for item in itens_mascarados] # Para debug
    }
    
    return contexto_agregado