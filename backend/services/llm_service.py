# backend/services/llm_service.py

import os
import json
import httpx
from typing import Dict, Any, Optional

from ..llm_optimization import ContextSummaryResponse, get_context_summary_prompt

from .policy_service import policy_service 

# --- Configuração do Endpoint Customizado (Lido de Variável de Ambiente) ---
CUSTOM_LLM_URL = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:11434/api/generate")

http_client = httpx.AsyncClient(timeout=30.0) 

# --- Função de FALLBACK (Retorna None) ---
def llm_fallback(raw_context: str) -> None:
    """Função de fallback. Não retorna mock, apenas None."""
    print("🧠 [LLM-FALLBACK] O serviço da LLM falhou e o mock foi removido.")
    return None

# --- Implementação REAL Assíncrona ---
async def analyze_context_with_llm_real(raw_context: str) -> Optional[ContextSummaryResponse]:
    """
    Implementação REAL da análise de contexto.
    Retorna ContextSummaryResponse em sucesso, ou None em falha.
    """
    
    masked_context = policy_service.apply_pcc_policies(raw_context)
    print("📡 [LLM-CUSTOM] Chamando endpoint: %s. Contexto mascarado aplicado." % CUSTOM_LLM_URL)
    
    prompt = get_context_summary_prompt(masked_context)
    payload = {
        "model": "flowmaster-agent-model",
        "prompt": prompt,
        "raw_context_len": len(raw_context),
    }

    try:
        response = await http_client.post(CUSTOM_LLM_URL, json=payload)
        response.raise_for_status()

        response_data = response.json()
        json_string = response_data.get("response") or response_data.get("text") or response.text.strip()
        
        if not json_string:
             raise ValueError("Resposta da LLM está vazia ou mal formatada.")

        data_dict = json.loads(json_string)
        
        return ContextSummaryResponse.model_validate(data_dict)

    except httpx.RequestError as e:
        print(f"❌ [LLM-CUSTOM] Erro de conexão ou HTTP com {CUSTOM_LLM_URL}: {e}. Retornando None.")
        return llm_fallback(raw_context) 
        
    except Exception as e:
        print(f"❌ [LLM-CUSTOM] Erro na resposta, validação Pydantic ou Policy: {e}. Retornando None.")
        return llm_fallback(raw_context)