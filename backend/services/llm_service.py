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
        # URL do Open WebUI (com /v1 para compatibilidade OpenAI)
        # Ex: http://ctb.qualbet.top:3000/api/v1 (ou apenas /v1 se for direto no Ollama)
        # Se usar Open WebUI: http://ctb.qualbet.top:3000/ollama/v1 ou /api/v1
        self.base_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:3000/api") 
        self.api_key = os.environ.get("LLM_API_KEY", "sk-fake-key") # Open WebUI exige Bearer, mesmo que fake
        self.model = os.environ.get("LLM_MODEL", "llama3")
        self.timeout = 60.0

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        """
        Gera resposta usando a API de Chat Completions (Padrão OpenAI/Open WebUI).
        """
        try:
            safe_prompt_log = security_service.mask_sensitive_data(prompt)
            logger.info(f"📤 [LLM] Prompt: {safe_prompt_log[:100]}...")

            context_str = json.dumps(context, ensure_ascii=False) if context else "N/A"
            
            system_message = f"""
            Você é o FlowMaster AI, um assistente corporativo.
            CONTEXTO ATUAL: {context_str}
            
            REGRAS:
            1. Responda APENAS o solicitado.
            2. Se for pedido JSON, não use markdown (```json). Retorne apenas o objeto raw.
            """

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            # Endpoint padrão de Chat Completions
            endpoint = f"{self.base_url}/chat/completions"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "stream": False,
                "response_format": {"type": "json_object"} if json_mode else None
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                if response.status_code == 404:
                    # Tenta fallback para rota do Ollama puro se o Open WebUI falhar
                    return await self._fallback_ollama_generate(prompt, context_str, json_mode)

                response.raise_for_status()
                result = response.json()
                
                # Extrai resposta do formato OpenAI
                content = result['choices'][0]['message']['content']
                
                if json_mode:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return self._get_mock_fallback(json_mode)
                
                return {"text": content}

        except Exception as e:
            logger.error(f"❌ [LLM] URL: {self.base_url}, Erro: {e}")
            return self._get_mock_fallback(json_mode)

    async def _fallback_ollama_generate(self, prompt, context_str, json_mode):
        """Fallback para API nativa do Ollama (/api/generate)"""
        try:
            logger.info("🔄 [LLM] Tentando fallback para API nativa do Ollama...")
            # Ajusta URL para porta do Ollama se necessário
            url = "[http://ctb.qualbet.top:11434/api/generate](http://ctb.qualbet.top:11434/api/generate)"
            
            payload = {
                "model": self.model,
                "prompt": f"Contexto: {context_str}\nInstrução: {prompt}",
                "stream": False,
                "format": "json" if json_mode else None
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    if json_mode:
                        return json.loads(data['response'])
                    return {"text": data['response']}
        except Exception as ex:
            logger.error(f"❌ [LLM] Fallback falhou: {ex}")
        
        return self._get_mock_fallback(json_mode)

    def _get_mock_fallback(self, json_mode: bool) -> Dict[str, Any]:
        if json_mode:
            return {
                "is_suggested": False, 
                "suggestions": [], 
                "reason": "IA Indisponível"
            }
        return {"text": "IA Indisponível."}

# Wrapper
async def analyze_context_with_llm_real(message: str, context: Dict[str, Any] = None) -> Any:
    service = LLMService()
    result = await service.generate_response(message, context=context, json_mode=False)
    
    class LLMResponseMock:
        def __init__(self, text):
            self.summary_analysis = text

    return LLMResponseMock(result.get("text", "Sem resposta."))