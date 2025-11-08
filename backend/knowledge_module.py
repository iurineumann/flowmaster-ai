# backend/knowledge_module.py
import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
import numpy as np

# --- 1. Corpus de Conhecimento (Base de Dados) ---
KNOWLEDGE_BASE = {
    "doc_id_1": {
        "title": "Padrão de Qualidade: Checklist de Revisão de Código para Ambientes Cloud",
        "content": (
            "A adoção do Serverless exige uma verificação de security headers e tratamento de logs. "
            "É fundamental que toda pull request (PR) contendo código Serverless seja revisada "
            "para garantir que a função lambda tenha o perfil IAM mais restrito possível "
            "(Princípio do Mínimo Privilégio) e que todas as exceções estejam sendo logadas de forma "
            "estruturada (JSON) para consumo no Datadog/Splunk. Qualquer alteração em gateways de API "
            "deve ser aprovada pelo Arquiteto Sênior."
        )
    },
    "doc_id_2": {
        "title": "Protocolo de Comunicação de Crise (Cliente X)",
        "content": "Em caso de falha na integração de pagamento, notificar imediatamente o Gerente de Contas via Teams e o Arquiteto de Dados Sênior (Elena Santos). Não comunicar o cliente antes da correção."
    }
}

# --- 2. Modelo de Embedding ---
model = SentenceTransformer('all-MiniLM-L6-v2') 
KNOWLEDGE_CONTENTS = [item['content'] for item in KNOWLEDGE_BASE.values()]
KNOWLEDGE_IDS = list(KNOWLEDGE_BASE.keys())

# Geração de Embeddings (Vetores) da Base de Conhecimento
print("Gerando Embeddings da Base de Conhecimento...")
try:
    KNOWLEDGE_EMBEDDINGS = model.encode(KNOWLEDGE_CONTENTS, convert_to_tensor=True)
    print("Embeddings gerados com sucesso.")
except Exception as e:
    # Este erro pode ocorrer se o ambiente Docker não tiver torch/transformers
    # Reiniciar o container com build garante que as dependências estejam instaladas.
    print(f"Erro ao gerar embeddings: {e}. Certifique-se de que 'torch' e 'sentence-transformers' estão instalados.")
    KNOWLEDGE_EMBEDDINGS = None


def find_relevant_document(query_text: str, top_k: int = 1) -> List[Dict[str, Any]]:
    """
    Busca documentos relevantes na base de conhecimento usando Similaridade de Cosseno.
    """
    if KNOWLEDGE_EMBEDDINGS is None:
        return []

    query_embedding = model.encode(query_text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, KNOWLEDGE_EMBEDDINGS)[0]
    top_results = torch.topk(cosine_scores, k=top_k)
    
    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        doc_id = KNOWLEDGE_IDS[idx.item()]
        doc_info = KNOWLEDGE_BASE[doc_id]
        
        results.append({
            "score": f"{score.item():.4f}",
            "title": doc_info['title'],
            "content_preview": doc_info['content'][:150] + "...",
            "doc_id": doc_id
        })
        
    return results