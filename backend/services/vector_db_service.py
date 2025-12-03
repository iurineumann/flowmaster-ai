# backend/services/vector_db_service.py

import os
import logging
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VectorDBService:
    """
    Gerencia a persistência e busca semântica de documentos usando ChromaDB.
    Utiliza um modelo local (SentenceTransformers) para gerar embeddings,
    garantindo que dados não saiam da infraestrutura para vetorização.
    """

    def __init__(self):
        self.persist_directory = os.path.join(os.getcwd(), "chroma_db_data")
        
        # Inicializa Cliente Persistente
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Função de Embedding (Executa localmente na CPU/GPU do container)
        # 'all-MiniLM-L6-v2' é rápido e eficiente para RAG geral
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Garante a criação da coleção principal
        self.collection = self.client.get_or_create_collection(
            name="flowmaster_knowledge_base",
            embedding_function=self.embedding_fn
        )
        logger.info(f"✅ [VectorDB] ChromaDB inicializado em {self.persist_directory}")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """
        Adiciona ou atualiza documentos no banco vetorial.
        """
        try:
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"💾 [VectorDB] {len(documents)} documentos indexados.")
        except Exception as e:
            logger.error(f"❌ [VectorDB] Erro ao indexar: {e}")
            raise

    async def search_relevant(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Realiza busca semântica por similaridade.
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k
            )
            
            # Formata resposta do ChromaDB para uma lista de dicts limpa
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    formatted_results.append({
                        "content": doc,
                        "metadata": meta,
                        "score": results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted_results

        except Exception as e:
            logger.error(f"❌ [VectorDB] Erro na busca: {e}")
            return []

# Singleton
vector_db = VectorDBService()

# Wrapper para compatibilidade com código legado/imports diretos
async def find_relevant_document_real(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    return await vector_db.search_relevant(query_text, top_k)