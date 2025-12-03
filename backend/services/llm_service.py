# backend/services/llm_service.py

import os
import httpx
import json
import logging
from typing import Dict, Any, Optional
from ..utils.data_security import security_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:11434/api/generate")
        self.model = os.environ.get("LLM_MODEL", "llama3")
        self.timeout = 60.0

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        """
        Envia prompt para LLM com fallback automático em caso de falha.
        """
        try:
            # 1. Sanitização (Logs)
            safe_prompt_log = security_service.mask_sensitive_data(prompt)
            logger.info(f"📤 [LLM] Prompt: {safe_prompt_log[:100]}...")

            context_str = json.dumps(context, ensure_ascii=False) if context else "N/A"
            
            full_prompt = f"""
            Você é o FlowMaster AI.
            CONTEXTO: {context_str}
            INSTRUÇÃO: {prompt}
            RESPOSTA: Apenas JSON válido.
            """

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "format": "json" if json_mode else None,
                "options": {"temperature": 0.2}
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload)
                
                # ✅ CORREÇÃO: Tratamento específico para 404 (URL/Modelo errado)
                if response.status_code == 404:
                    logger.error(f"❌ [LLM] Endpoint não encontrado (404): {self.api_url}")
                    return self._get_mock_fallback(json_mode)
                
                response.raise_for_status()
                result = response.json()
                raw_response = result.get("response", "")
                
                if json_mode:
                    try:
                        return json.loads(raw_response)
                    except json.JSONDecodeError:
                        return self._get_mock_fallback(json_mode)
                
                return {"text": raw_response}

        except Exception as e:
            logger.error(f"❌ [LLM] Erro Crítico: {e}")
            return self._get_mock_fallback(json_mode)

    def _get_mock_fallback(self, json_mode: bool) -> Dict[str, Any]:
        """Retorna uma resposta simulada para não quebrar o frontend."""
        logger.warning("⚠️ [LLM] Usando resposta de FALLBACK (Mock).")
        if json_mode:
            return {
                "is_suggested": False,
                "is_required": False,
                "suggestions": [],
                "reason": "Serviço de IA temporariamente indisponível (Modo Offline)."
            }
        return {"text": "Serviço de IA indisponível no momento."}

# Wrapper
async def analyze_context_with_llm_real(message: str, context: Dict[str, Any] = None) -> Any:
    service = LLMService()
    result = await service.generate_response(f"Responda: {message}", context=context, json_mode=False)
    
    class LLMResponseMock:
        def __init__(self, text):
            self.summary_analysis = text

    return LLMResponseMock(result.get("text", "Serviço indisponível."))