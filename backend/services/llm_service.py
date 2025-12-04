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
        # 1. Configuração da URL (Com limpeza robusta)
        raw_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:3000/ollama/v1")
        
        # Extração via Regex para garantir protocolo e host corretos
        match = re.search(r'(https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/[a-zA-Z0-9_./-]*)?)', raw_url)
        
        if match:
            self.base_url = match.group(1)
        else:
            self.base_url = raw_url.strip().strip('"').strip("'")

        # Normalização para Open WebUI (Rota OpenAI)
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]

        # Ajuste automático de rota /api -> /ollama/v1 para compatibilidade
        if "/ollama/v1" not in self.base_url and "/v1" not in self.base_url:
             if "/api" in self.base_url:
                 self.base_url = self.base_url.replace("/api", "/ollama/v1")
             else:
                 self.base_url = f"{self.base_url}/ollama/v1"

        logger.info(f"🔧 [LLM Config] URL Ativa: {self.base_url}")

        self.api_key = os.environ.get("LLM_API_KEY", "sk-no-key-required")
        self.model = os.environ.get("LLM_MODEL", "llama3.2:latest")
        self.timeout = 90.0 # Aumentado para dar tempo da Pesquisa Web acontecer

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        try:
            # Sanitização
            safe_prompt_log = security_service.mask_sensitive_data(prompt)
            logger.info(f"📤 [LLM] Prompt: {safe_prompt_log[:50]}...")

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

            endpoint = f"{self.base_url}/chat/completions"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": 0.2
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"❌ [LLM] Erro API {response.status_code}: {response.text}")
                    return self._fallback(json_mode, f"Erro HTTP {response.status_code}")

                result = response.json()
                
                # Extração de conteúdo
                content = ""
                try:
                    content = result['choices'][0]['message']['content']
                except (KeyError, IndexError):
                    content = result.get('response', '')

                if json_mode:
                    return self._parse_json(content)
                
                return {"text": content}

        except Exception as e:
            logger.error(f"❌ [LLM] Exceção: {e}")
            return self._fallback(json_mode, "Serviço Offline")

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """
        Extrai JSON de forma cirúrgica, ignorando logs de ferramentas (Web Search/Interpreter).
        """
        try:
            # 1. Tenta parse direto
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # 2. Tenta encontrar o bloco JSON entre ```json ... ```
                match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
                
                # 3. Tenta encontrar o primeiro '{' e o último '}' (Fallback para logs misturados)
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = content[start:end]
                    return json.loads(json_str)
                
                raise ValueError("Nenhum JSON encontrado no texto")
            except Exception as e:
                logger.warning(f"⚠️ [LLM] Falha no JSON Parse. Conteúdo bruto: {content[:100]}... Erro: {e}")
                return {"text": content, "error": "invalid_json_format"}

    def _fallback(self, json_mode: bool, reason: str) -> Dict[str, Any]:
        if json_mode:
            return {"suggestions": [], "is_suggested": False, "reason": reason}
        return {"text": f"Erro: {reason}"}

# Wrapper
async def analyze_context_with_llm_real(message: str, context: Dict[str, Any] = None) -> Any:
    service = LLMService()
    result = await service.generate_response(message, context=context, json_mode=False)
    class Mock:
        def __init__(self, t): self.summary_analysis = t
    return Mock(result.get("text", "Sem resposta."))