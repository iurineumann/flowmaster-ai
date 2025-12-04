# backend/services/vector_db_service.py

import os
import logging
import time
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from filelock import FileLock, Timeout # ✅ Import do FileLock

logger = logging.getLogger(__name__)

class VectorDBService:
    """
    Gerencia a persistência e busca semântica usando ChromaDB.
    Usa FileLock para garantir que apenas UM processo worker realize
    a migração/inicialização do banco de dados SQLite por vez.
    """

    def __init__(self):
        self.persist_directory = os.path.join(os.getcwd(), "chroma_db_data")
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.collection_name = "flowmaster_knowledge_base"
        
        # ✅ BLOQUEIO DE ARQUIVO PARA INICIALIZAÇÃO SEGURA
        # Isso impede que 5 workers tentem criar tabelas SQLite ao mesmo tempo.
        lock_file_path = os.path.join(self.persist_directory, "init.lock")
        lock = FileLock(lock_file_path, timeout=120) # 2 minutos de timeout
        
        logger.info("🔒 [VectorDB] Aguardando lock para inicialização segura...")
        
        try:
            with lock:
                logger.info("🔑 [VectorDB] Lock adquirido. Inicializando ChromaDB...")
                
                # Inicializa Cliente Persistente (Migrações rodam aqui)
                self.client = chromadb.PersistentClient(path=self.persist_directory)
                
                # Função de Embedding
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                
                # Garante a coleção
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
                logger.info("✅ [VectorDB] Inicialização concluída com sucesso.")
                
        except Timeout:
            logger.critical("❌ [VectorDB] Timeout ao aguardar lock do banco vetorial!")
            raise RuntimeError("Falha crítica na inicialização do VectorDB (Lock Timeout)")
        except Exception as e:
            logger.error(f"❌ [VectorDB] Erro fatal na inicialização: {e}")
            raise

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
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
try:
    vector_db = VectorDBService()
except Exception as e:
    logger.error(f"Falha ao instanciar Singleton VectorDB: {e}")
    vector_db = None

# Wrapper
async def find_relevant_document_real(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    if vector_db:
        return await vector_db.search_relevant(query_text, top_k)
    return []