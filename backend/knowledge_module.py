# backend/knowledge_module.py

from pydantic import BaseModel
from typing import List, Dict, Any
import time

# --- Modelos Pydantic para o Resultado da Busca (K-Search) ---
class KnowledgeSuggestion(BaseModel):
    """Modelo para um documento encontrado pelo K-Search."""
    title: str
    summary: str
    score: float # Score de similaridade (0.0 a 1.0)
    source: str  # Ex: 'Confluence', 'GitLab Wiki', 'Documentação'
    link: str

# --- Função de Busca de Conhecimento (Simulada) ---
def find_relevant_document(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Simula um serviço de Busca de Conhecimento (K-Search) usando embedding e busca vetorial.
    
    Recebe o texto do problema e retorna os documentos mais relevantes do Knowledge Base.
    """
    
    print(f"🧠 [K-SEARCH] Iniciando busca vetorial para: '{query_text[:50]}...'")
    
    # 📝 Simulação da Lógica de Similaridade:
    # Baseado no mock de graph_mock.py, sabemos que o foco é 'criptografia' e 'pagamento'.
    
    # Simula latência de processamento de IA/Busca (Comentado para agilizar o mock de desenvolvimento)
    # time.sleep(0.5) 

    if "criptografia" in query_text.lower() or "pagamento" in query_text.lower():
        results = [
            KnowledgeSuggestion(
                title="Protocolo V3 de Criptografia de Pagamentos - Guia",
                summary="Documentação oficial sobre a migração para o novo padrão de segurança V3, incluindo rotação de chaves e tratamento de PCI DSS.",
                score=0.95, # Alta similaridade
                source="Confluence",
                link="https://docs.flowmaster.ai/confluence/crypto-v3-guide"
            ).dict(),
            KnowledgeSuggestion(
                title="Checklist de Debugging de Falhas de Gateway",
                summary="Lista de verificação passo a passo para diagnosticar erros 500 em transações de pagamento via Gateway_Alpha.",
                score=0.88,
                source="GitLab Wiki",
                link="https://gitlab.flowmaster.ai/wiki/gateway-alpha-checklist"
            ).dict(),
            KnowledgeSuggestion(
                title="Procedimento de Reserva de Sala de Foco (SOP)",
                summary="Como reservar a Focus Room no 10º andar.",
                score=0.20, # Baixa relevância para o problema
                source="Documentação Interna",
                link="https://docs.flowmaster.ai/sop/reserva-salas"
            ).dict(),
        ]
    else:
        # Resultado genérico
        results = [
            KnowledgeSuggestion(
                title="FAQ Geral de Integração da API",
                summary="Respostas para dúvidas frequentes sobre como consumir a API principal.",
                score=0.65,
                source="Documentação Interna",
                link="https://docs.flowmaster.ai/faq/api"
            ).dict()
        ]

    # Retorna apenas os top_k resultados
    return results[:top_k]