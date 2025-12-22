# backend/llm_connector.py (FINAL COM TUNING DE CPU E TIMEOUTS)
import requests
from pydantic import BaseModel
from typing import List
import json

# Estrutura do item de contexto bruto
class RawContextItem(BaseModel):
    subject_or_title: str
    content_preview: str

class LLMConnector:
    """
    Conexão REAL com o LLM On-Premise (Ollama API), com tuning para CPU.
    """

    # CONFIGURAÇÕES DE PERFORMANCE
    LLM_TIMEOUT_SECONDS = 600  # Aumentado para 600s para maior estabilidade
    DEFAULT_CONTEXT_WINDOW = 4096 
    CPU_THREADS = 4 # Otimização de CPU: Ajuste para o número de cores da sua VM se for maior que 4
    
    # Modelo quantizado para melhor performance em CPU
    MODEL_NAME = "mistral:7b-instruct-q4_K_M" 

    def __init__(self, host: str = "http://ctb.qualbet.top:11434"): 
        self.host = host
        self.model = self.MODEL_NAME
        print(f"LLMConnector inicializado. Modelo: {self.model}. Timeout: {self.LLM_TIMEOUT_SECONDS}s.")

    def analyze_and_summarize_context(self, items: List[RawContextItem], user_name: str) -> str:
        
        # 1. Cria o Prompt
        raw_context = "\n".join([f"Item: {i.subject_or_title} - Conteúdo: {i.content_preview}" for i in items])
        prompt = (
            f"Analise os seguintes itens de comunicação do usuário {user_name}. "
            f"Qual é o foco crítico imediato (máximo 1 parágrafo) e qual solução a IA recomendaria? "
            f"Contexto Bruto: \n{raw_context}"
        )
        
        return self._call_ollama_api(prompt, temperature=0.3)

    def generate_rag_summary(self, document_content: str, focus_query: str) -> str:
        """
        Gera um resumo do documento de conhecimento (document_content) 
        focado na query do usuário (focus_query).
        """
        
        # Tuning: Instrução estrita para 3 frases, reduzindo o esforço do LLM
        prompt = (
            f"Você é um especialista em conhecimento. Use SOMENTE o conteúdo do documento abaixo para "
            f"escrever um resumo **claro de no máximo 3 frases** que resolva ou seja relevante para o foco crítico do usuário: '{focus_query}'.\n\n"
            f"CONTEÚDO DO DOCUMENTO: {document_content}"
        )
        
        return self._call_ollama_api(prompt, temperature=0.2)

    def _call_ollama_api(self, prompt: str, temperature: float) -> str:
        """Função auxiliar para fazer a chamada real à API do Ollama com tuning de CPU."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": self.DEFAULT_CONTEXT_WINDOW, 
                "num_thread": self.CPU_THREADS # Tuning de CPU
            }
        }
        
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.LLM_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "Erro: O LLM não retornou uma resposta válida.")

        except requests.exceptions.Timeout:
            # Retorno de erro mais claro em caso de timeout
            return f"Erro: Timeout ({self.LLM_TIMEOUT_SECONDS}s) com o LLM On-Premise. Aumente o timeout ou otimize o LLM."
        except requests.exceptions.RequestException as e:
            return f"Erro LLM On-Premise: Falha de conexão/API. ({type(e).__name__})"
        
llm_connector = LLMConnector()