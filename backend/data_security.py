# backend/data_security.py (Data Ingestion Layer - DIL)
import re
from typing import List

from .services.graph_repository import RawContextItem

def mask_pii_string(text: str) -> str:
    """
    Mascaramento baseado em regras (RegEx) para proteger PII simples.
    Substitui emails, números de telefone e IDs internos/documentos.
    """
    # 1. Mascarar endereços de e-mail (user@domain.com)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  '[EMAIL_MASKED]', 
                  text)
    
    # 2. Mascarar números de telefone (formatos comuns: (XX) XXXX-XXXX, XXXX-XXXX, etc.)
    text = re.sub(r'(\(?\d{2}\)?\s)?\d{4,5}[-\s]\d{4}', 
                  '[PHONE_MASKED]', 
                  text)

    # 3. Mascarar IDs ou CPFs fictícios (simulando documentos ou códigos internos)
    # Exemplo: 123.456.789-00 ou ID-456789
    text = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', 
                  '[DOC_ID_MASKED]', 
                  text)
    
    return text

def process_and_mask_raw_data(items: List[RawContextItem]) -> List[RawContextItem]:
    """
    Aplica o mascaramento a todos os itens de contexto antes de enviá-los ao LLM.
    """
    masked_items = []
    for item in items:
        # Mascara o conteúdo principal
        masked_content = mask_pii_string(item.content_preview)
        
        # Mascara o título (se houver PII)
        masked_title = mask_pii_string(item.subject_or_title)
        
        # Cria um novo objeto RawContextItem com os dados mascarados
        masked_item = item.copy(update={
            "content_preview": masked_content,
            "subject_or_title": masked_title
        })
        masked_items.append(masked_item)
        
    return masked_items