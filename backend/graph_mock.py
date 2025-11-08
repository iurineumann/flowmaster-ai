# backend/graph_mock.py
from pydantic import BaseModel
from typing import List

# Estrutura do item de Contexto Bruto (e-mail, chat ou reunião)
class RawContextItem(BaseModel):
    """Modelo para um item de dado bruto extraído do MS Graph."""
    item_id: str
    item_type: str  # e.g., 'email', 'chat', 'meeting'
    source: str     # e.g., 'Outlook', 'Teams'
    timestamp: str
    subject_or_title: str
    sender_or_creator: str
    # O campo crucial para a IA é o Tag do Projeto (ex: [CLIENTE_X] ou um ID de Projeto)
    project_tag: str 
    content_preview: str # O texto que a IA vai ler

# Dados MOCKADOS para simular a resposta da API do Microsoft Graph
MOCK_RAW_DATA: List[RawContextItem] = [
    RawContextItem(
        item_id="e1", 
        item_type="email", 
        source="Outlook", 
        timestamp="2025-11-10T09:00:00Z",
        subject_or_title="[CLIENTE_X] BUG CRÍTICO - Falha na Integração de Pagamento",
        sender_or_creator="gerente@empresa.com",
        project_tag="CLIENTE_X",
        content_preview="Precisamos de um desenvolvedor sênior para analisar o log de erros e corrigir o fluxo de pagamento antes do final do dia."
    ),
    RawContextItem(
        item_id="t1", 
        item_type="chat", 
        source="Teams", 
        timestamp="2025-11-10T10:15:00Z",
        subject_or_title="Canal: CLIENTE_X - Discussão de Solução",
        sender_or_creator="parceiro@empresa.com",
        project_tag="CLIENTE_X",
        content_preview="A Elena sugeriu usar a nova biblioteca de criptografia que ela desenvolveu. Isso pode resolver o problema de segurança no pagamento."
    ),
    RawContextItem(
        item_id="m1", 
        item_type="meeting", 
        source="Outlook", 
        timestamp="2025-11-10T14:00:00Z",
        subject_or_title="Daily Standup (Projeto Y)",
        sender_or_creator="pm@empresa.com",
        project_tag="PROJETO_Y",
        content_preview="Agenda: Revisão dos testes de UI, atualização de status e alinhamento de riscos."
    ),
]