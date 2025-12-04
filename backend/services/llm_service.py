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
        # 1. Leitura e Limpeza da URL
        raw_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:3000/api")
        
        # Regex para extrair apenas a URL base http(s)://host:port/path
        # Ignora aspas, espaços e sufixos indesejados
        match = re.search(r'https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/[a-zA-Z0-9_./-]*)?', raw_url)
        
        if match:
            clean_url = match.group(0)
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            self.base_url = clean_url
            logger.info(f"🔧 [LLM Config] URL Ativa: {self.base_url}")
        else:
            logger.critical(f"❌ [LLM Config] URL inválida: {raw_url}. Usando fallback.")
            self.base_url = "http://ctb.qualbet.top:3000/api"

        self.api_key = os.environ.get("LLM_API_KEY", "sk-no-key-required")
        self.model = os.environ.get("LLM_MODEL", "llama3")
        self.timeout = 60.0

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        """
        Gera resposta usando a API Open WebUI.
        """
        try:
            # 1. Sanitização de Logs
            safe_prompt_log = security_service.mask_sensitive_data(prompt)
            logger.info(f"📤 [LLM] Prompt: {safe_prompt_log[:50]}...")

            context_str = json.dumps(context, ensure_ascii=False) if context else "N/A"
            
            # 2. System Prompt (Reforçado para JSON)
            system_instruction = ""
            if json_mode:
                system_instruction = "IMPORTANTE: Sua resposta deve ser EXCLUSIVAMENTE um objeto JSON válido. Não use markdown, não use explicações antes ou depois."

            system_message = f"""
            Você é o FlowMaster AI.
            CONTEXTO: {context_str}
            INSTRUÇÃO: {prompt}
            {system_instruction}
            """

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            # 3. Construção do Endpoint
            # Se a URL base já terminar em /v1 (comum no Ollama), ajustamos
            if self.base_url.endswith("/v1"):
                endpoint = f"{self.base_url}/chat/completions"
            else:
                # Open WebUI padrão
                endpoint = f"{self.base_url}/chat/completions"

            # 4. Payload Compatível (Sem parâmetros experimentais)
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "stream": False
                # REMOVIDO: "response_format": {"type": "json_object"} 
                # Motivo: Causa erro 400 em versões do Ollama/WebUI que não suportam nativamente.
                # Confiamos no System Prompt para formatar o JSON.
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                if response.status_code != 200:
                    error_msg = f"Status {response.status_code} - {response.text}"
                    logger.error(f"❌ [LLM] Erro API: {error_msg} ({self.model})")
                    
                    # Tratamento especial para 404 (Rota incorreta)
                    if response.status_code == 404:
                        logger.warning("⚠️ Tentando rota alternativa /ollama/v1...")
                        return await self._try_fallback_route(messages, json_mode)
                        
                    return self._fallback(json_mode, error_msg)

                result = response.json()
                
                # Extração segura
                try:
                    content = result['choices'][0]['message']['content']
                except (KeyError, IndexError):
                    content = result.get('response', '')

                if json_mode:
                    return self._parse_json(content)
                
                return {"text": content}

        except Exception as e:
            logger.error(f"❌ [LLM] Exceção: {e}")
            return self._fallback(json_mode, "Erro interno de conexão")

    async def _try_fallback_route(self, messages, json_mode):
        """Tenta a rota direta do Ollama via WebUI se a rota /api falhar"""
        try:
            # Tenta ajustar a URL para o proxy do Ollama dentro do WebUI
            base = self.base_url.replace("/api", "/ollama/api")
            endpoint = f"{base}/chat"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "format": "json" if json_mode else None
            }
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get('message', {}).get('content', '')
                    if json_mode:
                        return self._parse_json(content)
                    return {"text": content}
        except:
            pass
        return self._fallback(json_mode, "Todas as rotas falharam")

    def _parse_json(self, content: str) -> Dict[str, Any]:
        try:
            # Limpa blocos de código markdown ```json ... ```
            clean_content = re.sub(r'```json\s*|\s*```', '', content).strip()
            # Limpa quebras de linha extras que podem quebrar o json.loads
            return json.loads(clean_content)
        except json.JSONDecodeError:
            logger.warning(f"⚠️ [LLM] Falha no JSON Parse. Conteúdo recebido: {content[:100]}...")
            return {"text": content, "error": "invalid_json_format"}

    def _fallback(self, json_mode: bool, reason: str) -> Dict[str, Any]:
        if json_mode:
            return {
                "is_suggested": False, 
                "suggestions": [], 
                "reason": f"Modo Offline ({reason})"
            }
        return {"text": f"IA Indisponível: {reason}"}

# Wrapper
async def analyze_context_with_llm_real(message: str, context: Dict[str, Any] = None) -> Any:
    service = LLMService()
    result = await service.generate_response(message, context=context, json_mode=False)
    
    class LLMResponseMock:
        def __init__(self, text):
            self.summary_analysis = text

    return LLMResponseMock(result.get("text", "Sem resposta."))