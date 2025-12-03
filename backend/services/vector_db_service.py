# backend/services/vector_db_service.py

import os
import logging
import time
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VectorDBService:
    """
    Gerencia a persistência e busca semântica de documentos usando ChromaDB.
    Inclui lógica robusta de inicialização para suportar múltiplos workers do Gunicorn.
    """

    def __init__(self):
        self.persist_directory = os.path.join(os.getcwd(), "chroma_db_data")
        
        # Inicializa Cliente Persistente
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Função de Embedding
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection_name = "flowmaster_knowledge_base"
        self.collection = self._initialize_collection_safely()
        
        logger.info(f"✅ [VectorDB] ChromaDB inicializado em {self.persist_directory}")

    def _initialize_collection_safely(self):
        """
        Tenta obter ou criar a coleção lidando com condições de corrida (Race Conditions)
        entre múltiplos workers do Gunicorn.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Tenta obter a coleção existente primeiro
                return self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
            except Exception:
                # Se não existe, tenta criar
                try:
                    return self.client.create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_fn
                    )
                except Exception as e:
                    # Se falhar na criação (ex: outro worker criou nesse meio tempo),
                    # espera um pouco e tenta obter novamente na próxima iteração
                    logger.warning(f"⚠️ [VectorDB] Concorrência detectada na criação (Tentativa {attempt+1}/{max_retries}): {e}")
                    time.sleep(1) # Breve pausa para deixar o lock do SQLite liberar
        
        # Se falhar após retries, tenta uma última vez obter (deve existir agora)
        return self.client.get_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )

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

# Wrapper para compatibilidade
async def find_relevant_document_real(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    return await vector_db.search_relevant(query_text, top_k)