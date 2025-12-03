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
        self.api_url = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:11434/api/generate")
        self.model = os.environ.get("LLM_MODEL", "llama3") 
        self.timeout = 60.0

    async def generate_response(self, prompt: str, context: Dict[str, Any] = None, json_mode: bool = True) -> Dict[str, Any]:
        """
        Envia um prompt para a LLM e retorna uma resposta estruturada.
        """
        try:
            full_prompt = f"""
            Você é o FlowMaster AI.
            CONTEXTO: {json.dumps(context, ensure_ascii=False) if context else "Nenhum"}
            TAREFA: {prompt}
            RESPOSTA: Apenas JSON válido.
            """

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "format": "json" if json_mode else None
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload)
                if response.status_code != 200:
                    logger.error(f"❌ [LLM] Erro HTTP {response.status_code}: {response.text}")
                    return {"error": "Serviço indisponível"}
                
                result = response.json()
                response_text = result.get("response", "")
                
                if json_mode:
                    try:
                        return json.loads(response_text)
                    except:
                        return {"text": response_text}
                
                return {"text": response_text}

        except Exception as e:
            logger.error(f"❌ [LLM] Erro: {e}")
            return {"error": "Erro interno na LLM"}

# ✅ Wrapper para compatibilidade com knowledge_module.py e chat.py
async def analyze_context_with_llm_real(message: str, context: Dict[str, Any] = None) -> Any:
    service = LLMService()
    # Se for chamado pelo Chat, queremos um resumo ou resposta direta
    prompt = f"Analise a mensagem do usuário e responda de forma útil: {message}"
    
    # Retorna um objeto simples compatível com o que o Chat espera (summary_analysis)
    result = await service.generate_response(prompt, context=context, json_mode=False)
    
    # Mock de estrutura de objeto para compatibilidade com código legado que espera atributos
    class LLMResponseMock:
        def __init__(self, text):
            self.summary_analysis = text

    return LLMResponseMock(result.get("text", "Não foi possível processar."))