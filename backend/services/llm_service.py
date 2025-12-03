# backend/services/llm_service.py

import os
import httpx
import json
import logging
import re
from typing import Dict, Any, Optional
from ..services.data_security import security_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # 1. Leitura da Variável
        raw_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:3000/api")
        
        # 2. Extração Robusta de URL (Regex)
        # Procura por http:// ou https:// seguido de caracteres válidos, ignorando [ ] ( ) ou espaços ao redor
        match = re.search(r'https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/[a-zA-Z0-9_./-]*)?', raw_url)
        
        if match:
            clean_url = match.group(0)
            # Garante que não termina com barra para padronizar concatenação
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            self.base_url = clean_url
            logger.info(f"🔧 [LLM Config] URL Extraída e Limpa: {self.base_url}")
        else:
            logger.critical(f"❌ [LLM Config] URL inválida no .env: {raw_url}. Usando fallback.")
            self.base_url = "http://ctb.qualbet.top:3000/api"

        # Chave de API (Obrigatória para Open WebUI, opcional para Ollama puro)
        self.api_key = os.environ.get("LLM_API_KEY", "sk-no-key-required")
        self.model = os.environ.get("LLM_MODEL", "llama3")
        self.timeout = 60.0

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        """
        Gera resposta usando a API Chat Completions (Padrão OpenAI/Open WebUI).
        """
        try:
            # Sanitização e Logs
            safe_prompt_log = security_service.mask_sensitive_data(prompt)
            # logger.debug(f"📤 [LLM] Prompt: {safe_prompt_log[:50]}...") # Debug apenas se necessário

            context_str = json.dumps(context, ensure_ascii=False) if context else "N/A"
            
            system_message = f"""
            Você é o FlowMaster AI.
            CONTEXTO: {context_str}
            INSTRUÇÃO: {prompt}
            """

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            # Construção do Endpoint (Compatível com Open WebUI e OpenAI)
            endpoint = f"{self.base_url}/chat/completions"
            
            # Validação Final de Segurança
            if not endpoint.startswith(("http://", "https://")):
                logger.error(f"❌ [LLM] Erro Crítico de Protocolo na URL final: {endpoint}")
                return self._fallback(json_mode, "Erro de Configuração de URL")

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
                    logger.error(f"❌ [LLM] 404 Not Found em: {endpoint}. Verifique o modelo '{self.model}' ou a URL.")
                    return self._fallback(json_mode, "Modelo ou Endpoint não encontrado")
                
                response.raise_for_status()
                result = response.json()
                
                try:
                    content = result['choices'][0]['message']['content']
                except (KeyError, IndexError, TypeError):
                    # Fallback para formato Ollama nativo se a resposta for diferente
                    content = result.get('response', '')

                if json_mode:
                    return self._parse_json(content)
                
                return {"text": content}

        except httpx.ConnectError:
            logger.error(f"❌ [LLM] Falha de Conexão com {self.base_url}. O serviço está online?")
            return self._fallback(json_mode, "Serviço de IA offline")
        except Exception as e:
            logger.error(f"❌ [LLM] Erro Genérico: {e} ({self.api_key})")
            return self._fallback(json_mode, "Erro interno na IA")

    def _parse_json(self, content: str) -> Dict[str, Any]:
        try:
            # Remove markdown code blocks se a LLM insistir em colocá-los
            clean_content = re.sub(r'```json\s*|\s*```', '', content).strip()
            return json.loads(clean_content)
        except json.JSONDecodeError:
            return {"text": content, "error": "invalid_json_format"}

    def _fallback(self, json_mode: bool, reason: str) -> Dict[str, Any]:
        if json_mode:
            return {
                "is_suggested": False, 
                "suggestions": [], 
                "reason": f"Modo Offline ({reason})"
            }
        return {"text": f"IA Indisponível: {reason}"}

# Wrapper de Compatibilidade
async def analyze_context_with_llm_real(message: str, context: Dict[str, Any] = None) -> Any:
    service = LLMService()
    result = await service.generate_response(message, context=context, json_mode=False)
    
    class LLMResponseMock:
        def __init__(self, text):
            self.summary_analysis = text

    return LLMResponseMock(result.get("text", "Sem resposta."))