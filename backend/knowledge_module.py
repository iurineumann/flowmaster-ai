# backend/knowledge_module.py (AGORA CONTÉM DADOS DE CONTEÚDO COMPLETO)
import random
from typing import List
from pydantic import BaseModel
from backend.llm_connector import llm_connector, RawContextItem 

class SugestaoConhecimento(BaseModel):
    score: str
    title: str
    # O content_preview será gerado pelo LLM em tempo real
    content_preview: str 
    doc_id: str
    # NOVO: Campo para armazenar o conteúdo completo do documento para a chamada RAG
    full_content: str = "" 


DOCUMENT_MOCK_DATABASE: List[SugestaoConhecimento] = [
    SugestaoConhecimento(
        score="0.98", 
        title="Protocolo de Segurança para Transações via Lambda", 
        doc_id="DOC_SEC_101",
        content_preview="", # Deixamos vazio, será preenchido pelo LLM
        full_content="O Protocolo IAM T2M v2.3 exige que todas as transações de pagamento usem criptografia AES-256 e que a chave seja rotacionada a cada 24 horas via AWS Secrets Manager. O log de erro atual do Cliente X indica falha na rotação da chave."
    ),
    SugestaoConhecimento(
        score="0.95", 
        title="Guia Rápido: Integração da Biblioteca de Criptografia Python", 
        doc_id="DOC_CRIP_205",
        content_preview="", # Deixamos vazio
        full_content="A biblioteca de criptografia `t2m-crypto-v2.1` resolve o problema de incompatibilidade com o novo protocolo AES-256. A instalação é via `pip install t2m-crypto-v2.1` e a função de correção de chave é `rotate_key_fix()`. Elena é a mantenedora do projeto."
    ),
    SugestaoConhecimento(
        score="0.82", 
        title="FAQ: Erros Comuns de Integração de Pagamento com Cliente X", 
        doc_id="DOC_FAQ_330",
        content_preview="", # Deixamos vazio
        full_content="A maioria dos erros de pagamento do Cliente X está relacionada a certificados SSL expirados ou falhas de timeout, e não ao problema de criptografia, que é um novo erro."
    ),
]


def find_relevant_document(query_text: str, top_k: int = 2) -> List[SugestaoConhecimento]:
    """
    Simula o K-Search (Busca de Conhecimento).
    A 'busca' ainda é mockada, mas o retorno é o objeto completo do documento.
    """
    
    # MOCK: A busca retorna os documentos mais relevantes para o foco de segurança/pagamento
    relevant_docs = sorted(
        [d for d in DOCUMENT_MOCK_DATABASE if "criptografia" in d.content_preview or "segurança" in d.title],
        key=lambda x: float(x.score),
        reverse=True
    )
    
    # Retorna os objetos com o full_content
    return relevant_docs[:top_k]

# A função de find_relevant_document continua como mock para o POC, apenas para retornar os dados completos.