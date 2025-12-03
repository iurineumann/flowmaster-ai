# backend/services/llm_service.py

import os
import httpx
import json
import logging
from typing import Dict, Any, Optional

# Configuração de Logger
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Lê a URL do .root.env (passado via docker-compose)
        self.api_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:11434/api/generate")
        self.model = os.environ.get("LLM_MODEL", "llama3") # Ou o modelo que você estiver usando
        self.timeout = 60.0 # Timeout mais longo para geração de texto

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        """
        Envia um prompt para a LLM e retorna uma resposta estruturada.
        """
        try:
            # Constrói o prompt enriquecido com contexto
            full_prompt = f"""
            Você é o FlowMaster AI, um assistente corporativo inteligente.
            
            CONTEXTO DO USUÁRIO:
            {json.dumps(context, indent=2, ensure_ascii=False) if context else "Nenhum contexto específico."}
            
            TAREFA:
            {prompt}
            
            FORMATO DE RESPOSTA:
            Responda EXCLUSIVAMENTE em JSON válido. Não inclua markdown (```json).
            """

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "format": "json" if json_mode else None
            }

            logger.info(f"📤 [LLM] Enviando requisição para {self.api_url}...")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get("response", "")
                
                logger.info("📥 [LLM] Resposta recebida com sucesso.")

                if json_mode:
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error(f"❌ [LLM] Falha ao decodificar JSON: {response_text}")
                        # Fallback simples
                        return {"error": "Falha na geração do JSON", "raw": response_text}
                
                return {"text": response_text}

        except httpx.RequestError as e:
            logger.error(f"❌ [LLM] Erro de conexão: {e}")
            return {"error": "Serviço de IA indisponível", "details": str(e)}
        except Exception as e:
            logger.error(f"❌ [LLM] Erro genérico: {e}")
            return {"error": "Erro interno no processamento de IA"}