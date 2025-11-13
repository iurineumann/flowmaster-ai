# backend/services/llm_service.py

import os
import json
import httpx
from typing import Dict, Any

# Importa o Pydantic Schema de otimização e o MOCK
from ..llm_optimization import ContextSummaryResponse, get_context_summary_prompt
from ..llm_optimization import MOCK_SUMMARY_RESPONSE 

# Importa o Policy Service e a sessão DB
from .policy_service import PolicyService, policy_service
from ..db.database import SessionLocal 

# --- Configuração do Endpoint Customizado (Lido de Variável de Ambiente) ---
# Configuração que permite a substituição do endpoint por .env
CUSTOM_LLM_URL = os.environ.get("CUSTOM_LLM_URL", "http://ctb.qualbet.top:11434/api/generate")

# O cliente HTTP é criado fora da função para reuso, mas a chamada é assíncrona
http_client = httpx.AsyncClient(timeout=30.0) 

# --- Função de MOCK/FALLBACK (Definida LOCALMENTE) ---
def mock_analyzer(raw_context: str) -> ContextSummaryResponse:
    """Função síncrona de mock/fallback. Retorna o mock estruturado de crise."""
    print("🧠 [LLM-FALLBACK] Usando MOCK de resposta da LLM.")
    return MOCK_SUMMARY_RESPONSE

# --- Implementação REAL Assíncrona ---
async def analyze_context_with_llm_real(raw_context: str) -> ContextSummaryResponse:
    """
    Implementação REAL da análise de contexto, com fallback robusto em caso de falha.
    """
    
    # 1. IMPLEMENTAÇÃO DO PCC AGENT (Mascaramento de Dados)
    db = SessionLocal()
    # A chamada real do Policy Service deve ser síncrona, usando a sessão do DB.
    # Assumindo que o mascaramento é síncrono.
    masked_context = policy_service.apply_pcc_policies(raw_context) 
    print("📡 [LLM-CUSTOM] Chamando endpoint: %s. Contexto mascarado aplicado." % CUSTOM_LLM_URL)
    
    # 2. Prepara o Payload para a LLM
    prompt = get_context_summary_prompt(masked_context)
    payload = {
        "model": "flowmaster-agent-model", # Nome do modelo que espera o JSON Schema
        "prompt": prompt,
        "raw_context_len": len(raw_context), # Apenas para logging
    }

    try:
        # 3. Chamada assíncrona real
        response = await http_client.post(CUSTOM_LLM_URL, json=payload)
        response.raise_for_status() # Lança erro para 4xx/5xx

        response_data = response.json()
        
        # Tenta extrair o texto JSON da resposta
        json_string = response_data.get("response") or response_data.get("text") or response.text.strip()
        
        if not json_string:
             raise ValueError("Resposta da LLM está vazia ou mal formatada.")

        # Tenta parsear a string JSON e validar com Pydantic
        data_dict = json.loads(json_string)
        
        # 4. Sucesso: Valida e retorna o objeto Pydantic
        return ContextSummaryResponse.model_validate(data_dict)

    except httpx.RequestError as e:
        # 5. ERRO: Conexão ou HTTP (Servidor Customizado Offline - 404/Connection Refused)
        print(f"❌ [LLM-CUSTOM] Erro de conexão ou HTTP com {CUSTOM_LLM_URL}: {e}. Retornando MOCK.")
        return mock_analyzer(raw_context) 
        
    except Exception as e:
        # 6. ERRO: Parsing JSON, Validação Pydantic ou Policy Service
        print(f"❌ [LLM-CUSTOM] Erro na resposta, validação Pydantic ou Policy: {e}. Retornando MOCK.")
        return mock_analyzer(raw_context)