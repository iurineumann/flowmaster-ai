# backend/services/vector_db_service.py

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import time

# --- Mock de Embeddings e Inicialização do Vector DB ---

class MockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Simula uma função de embedding real para testes (Ex: text-embedding-004)."""
    def __call__(self, texts: List[str]) -> List[List[float]]:
        # Gera um vetor baseado no tamanho do texto, apenas para simulação
        return [[len(text) * 0.01 for _ in range(384)] for text in texts]

client_chroma = chromadb.Client()
kb_collection = None # Será inicializado na função de busca

async def initialize_vector_db():
    """Inicializa e popula o Vector DB com os documentos de conhecimento."""
    global kb_collection
    collection_name = "flowmaster_knowledge_base"
    
    # Dados para o Knowledge Base
    DOCUMENTS = [
        {"id": "doc_01", "text": "Protocolo V3 de Criptografia de Pagamentos - Guia oficial de migração de chaves e tratamento de PCI DSS.", "source": "Confluence", "link": "https://docs.flowmaster.ai/confluence/crypto-v3-guide"},
        {"id": "doc_02", "text": "Checklist de Debugging de Falhas de Gateway Alpha para diagnosticar erros 500 em transações de pagamento.", "source": "GitLab Wiki", "link": "https://gitlab.flowmaster.ai/wiki/gateway-alpha-checklist"},
        {"id": "doc_03", "text": "Procedimento de Reserva de Sala de Foco (SOP).", "source": "Documentação Interna", "link": "https://docs.flowmaster.ai/sop/reserva-salas"},
    ]
    METADATAS = [{"source": d["source"], "link": d["link"], "title": d["text"].split(' - ')[0]} for d in DOCUMENTS]
    IDS = [d["id"] for d in DOCUMENTS]
    TEXTS = [d["text"] for d in DOCUMENTS]

    try:
        kb_collection = client_chroma.create_collection(
            name=collection_name, 
            embedding_function=MockEmbeddingFunction()
        )
        kb_collection.add(documents=TEXTS, metadatas=METADATAS, ids=IDS)
        print(f"🧠 [VECTOR DB] Knowledge Base mockada com {len(DOCUMENTS)} documentos.")
    except Exception:
        # Se a coleção já existir (após um reload), apenas a obtém
        kb_collection = client_chroma.get_collection(name=collection_name)
    
    return kb_collection

async def find_relevant_document_real(query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Busca REAL no Vector Database (ChromaDB) por similaridade, substituindo o mock.
    """
    global kb_collection
    if kb_collection is None:
        kb_collection = await initialize_vector_db()

    time.sleep(0.05) # Simula latência de busca

    try:
        results = kb_collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=['metadatas', 'documents', 'distances']
        )
        
        # Formata o output para o schema esperado (KnowledgeSuggestion)
        suggestions = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                document = results['documents'][0][i]
                # Converte a distância (menor é melhor) para score (maior é melhor)
                score = max(0.0, round(1.0 - results['distances'][0][i] / max(results['distances'][0]), 2))
                
                suggestions.append({
                    "title": metadata['title'],
                    "summary": document,
                    "score": score * 100, # Convertido para percentual
                    "source": metadata['source'],
                    "link": metadata['link']
                })
        
        return suggestions
        
    except Exception as e:
        print(f"❌ [K-SEARCH] Erro na busca do Vector DB: {e}")
        return []