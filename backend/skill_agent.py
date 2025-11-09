# backend/skill_agent.py
from pydantic import BaseModel
from typing import List, Optional

# Importa o conector LLM real para análise
from backend.llm_connector import llm_connector, RawContextItem 

class SkillSuggestionModel(BaseModel):
    # Modelo Pydantic para o retorno (alinhado com a interface do Frontend)
    type: str # 'course' | 'expert' | 'info'
    title: str
    context_reason: str

class SkillAgent:
    """
    Agente responsável por analisar o foco crítico e sugerir o próximo passo 
    para desenvolvimento de habilidades (Skill-Boost).
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        
    def get_suggestions(self, current_focus_tag: str) -> List[SkillSuggestionModel]:
        
        # 1. Simula a entrada de dados do usuário (Habilidades/Skills)
        user_skills_mock = "Python, DevOps (básico), SQL"
        
        # 2. Chamada ao LLM para Análise (Formulação do Foco)
        # Em um cenário real, o LLM compararia o 'foco' com as 'skills' do usuário.
        prompt = (
            f"O usuário (habilidades: {user_skills_mock}) tem como foco crítico: {current_focus_tag}. "
            f"O foco exige expertise em Criptografia e Segurança. Qual curso ou expert seria mais relevante?"
        )
        
        # Aqui, o LLM Connector seria chamado:
        # llm_response = llm_connector.analyze_and_summarize_context(
        #     items=[RawContextItem(subject_or_title=current_focus_tag, content_preview=prompt)],
        #     user_name=f"Usuário ID {self.user_id}"
        # )
        
        # MOCK DE DECISÃO: Retorna a sugestão que complementa o foco de 'BUG CRÍTICO/CRIPTOGRAFIA'
        if "CLIENTE_X" in current_focus_tag.upper():
            return [
                SkillSuggestionModel(
                    type="course",
                    title="Curso: Criptografia e Lambda Security",
                    context_reason="Foco crítico no bug de pagamento e falta de skill avançada em segurança."
                ),
                SkillSuggestionModel(
                    type="expert",
                    title="Dra. Elena Santos (Especialista em Cripto)",
                    context_reason="Mencionada no chat de Teams como detentora da solução de criptografia."
                )
            ]
        
        return []