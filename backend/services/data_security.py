# backend/utils/data_security.py

import re
import logging
from typing import  Dict, Any

logger = logging.getLogger(__name__)

class DataSecurityService:
    """
    Serviço centralizado para proteção de dados e conformidade com LGPD.
    Responsável por sanitizar logs e inputs de LLM.
    """

    # Padrões Regex para PII (Personal Identifiable Information)
    REGEX_PATTERNS = {
        'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
        'credit_card': r'\b(?:\d[ -]*?){13,16}\b'
    }

    @classmethod
    def mask_sensitive_data(cls, text: str) -> str:
        """
        Substitui informações sensíveis por placeholders [REDACTED].
        """
        if not text or not isinstance(text, str):
            return text

        masked_text = text
        for key, pattern in cls.REGEX_PATTERNS.items():
            masked_text = re.sub(pattern, f'[REDACTED_{key.upper()}]', masked_text)
        
        return masked_text

    @classmethod
    def sanitize_log_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma cópia sanitizada de um dicionário para fins de log.
        """
        try:
            sanitized = {}
            for k, v in payload.items():
                if isinstance(v, str):
                    sanitized[k] = cls.mask_sensitive_data(v)
                elif isinstance(v, dict):
                    sanitized[k] = cls.sanitize_log_payload(v)
                elif isinstance(v, list):
                    sanitized[k] = [cls.mask_sensitive_data(i) if isinstance(i, str) else i for i in v]
                else:
                    sanitized[k] = v
            return sanitized
        except Exception as e:
            logger.error(f"Erro ao sanitizar payload: {e}")
            return {"error": "Payload sanitization failed"}

# Instância singleton para uso direto
security_service = DataSecurityService()