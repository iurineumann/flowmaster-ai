# backend/context_agent.py
from typing import Dict, Any, List
# Importa o MOCK de dados (será substituído pelo MS Graph)
from backend.services.graph_repository import MOCK_RAW_DATA, RawContextItem
# Importa o conector LLM (agora configurado para http://ctb.qualbet.top:11434)
from backend.llm_connector import llm_connector 

class ContextAgent:
    """
    Agente responsável por agregar e processar dados brutos de comunicação 
    (MS Graph Mock) e gerar o Foco Crítico e Resumo de IA usando o LLM On-Premise.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        # Em um sistema real, aqui haveria a inicialização de credenciais de acesso

    def get_aggregated_context(self, project_tag: str = "CLIENTE_X") -> Dict[str, Any]:
        """
        Executa a lógica principal do Agente de Contexto.
        """
        
        # 1. Agregação de Dados Brutos (Filtra pelo tag do projeto)
        itens_do_foco: List[RawContextItem] = [
            item for item in MOCK_RAW_DATA if item.project_tag == project_tag
        ]

        if not itens_do_foco:
            return {
                "user_id": self.user_id,
                "foco_atual_titulo": "Nenhum Foco Imediato Detectado",
                "resumo_ia": "Aguardando dados de comunicação para análise.",
                "numero_itens_agregados": 0,
                "proxima_reuniao": "Nenhuma agendada.",
                "raw_items": [],
            }

        # 2. Chamada ao LLM para Geração de Resumo (O Coração da IA)
        # O LLM (Mistral On-Premise) recebe todos os itens brutos para resumir e extrair o foco.
        resumo_ia = llm_connector.analyze_and_summarize_context(
            items=itens_do_foco,
            user_name=f"Usuário ID {self.user_id}" 
        )
        
        # 3. Extração de Metadados (Mock de Próxima Reunião)
        proxima_reuniao = next(
            (item.subject_or_title for item in itens_do_foco if item.item_type == 'meeting'),
            "Nenhuma agendada."
        )

        # 4. Determinação do Título (Pega o título do item mais crítico/primeiro)
        foco_titulo = itens_do_foco[0].subject_or_title
        
        return {
            "user_id": self.user_id,
            "foco_atual_titulo": foco_titulo,
            "resumo_ia": resumo_ia, # Resumo gerado pelo LLM
            "numero_itens_agregados": len(itens_do_foco),
            "proxima_reuniao": proxima_reuniao,
            # Itens brutos são retornados temporariamente para serem usados pelo K-Search
            "raw_items": itens_do_foco,
        }