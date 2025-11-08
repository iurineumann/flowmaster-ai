# backend/skill_mock.py
from pydantic import BaseModel
from typing import List

# Estrutura de dados para o Skill-Boost
class SkillSuggestion(BaseModel):
    """Modelo para uma sugestão de desenvolvimento (curso/especialista)."""
    type: str # 'course' ou 'expert'
    title: str
    context_reason: str # Por que a IA sugeriu isso?

# MOCK DA BASE DE CONHECIMENTO DE SKILL-BOOST
# (Em uma versão real, isso seria um modelo de IA que sugere com base no GAP de habilidade)
SKILL_MOCK_DATABASE = {
    # Regra: Se o foco é "CLIENTE_X", sugere Segurança em AWS e Elena
    "CLIENTE_X": [
        SkillSuggestion(
            type="course",
            title="Curso Rápido: Segurança em AWS Lambda (30 min)",
            context_reason="O projeto CLIENTE_X lida com arquitetura serverless e requer validações de IAM."
        ),
        SkillSuggestion(
            type="expert",
            title="Dra. Elena Santos (Perfil IAM)",
            context_reason="Elena trabalhou no projeto anterior de criptografia e é especialista em IAM e segurança de microsserviços."
        )
    ],
    # Regra: Se o foco é "PROJETO_Y", sugere Testes de UI e Thiago
    "PROJETO_Y": [
        SkillSuggestion(
            type="course",
            title="Curso: Testes de UI/UX em React com Cypress",
            context_reason="O PROJETO_Y tem histórico de problemas em Testes de Interface e usabilidade."
        ),
        SkillSuggestion(
            type="expert",
            title="Thiago Almeida (QA Sênior)",
            context_reason="Thiago é o especialista em Testes de UI do PROJETO_Y e pode acelerar a resolução."
        )
    ]
}