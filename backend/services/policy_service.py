# backend/services/policy_service.py

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import re
from ..db import models
from ..db.database import get_db, SessionLocal

class PolicyService:
    """Serviço responsável por buscar e aplicar políticas de compliance e mascaramento."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_policies(self, module_id: Optional[str] = None) -> List[models.PolicyModel]:
        """Busca políticas globais e políticas específicas do módulo, se fornecido."""
        query = self.db.query(models.PolicyModel).filter(models.PolicyModel.is_active == True)
        
        # Filtra por global OU pelo ID do módulo
        if module_id:
            query = query.filter(
                (models.PolicyModel.applies_to == 'global') | 
                (models.PolicyModel.applies_to == module_id)
            )
        else:
            query = query.filter(models.PolicyModel.applies_to == 'global')
            
        return query.all()

    def apply_masking_policy(self, text: str, policies: List[models.PolicyModel]) -> str:
        """
        Aplica regras de mascaramento ao texto bruto antes de enviá-lo à LLM.
        """
        masked_text = text
        
        for policy in policies:
            rule = policy.policy_rule
            if rule and rule.get("action") == "mask":
                # Implementação de mascaramento baseada em REGEX (para CPF, CNPJ, Email, etc.)
                if rule.get("target_data") == "cpf":
                    # Simulação: Mascara CPFs (padrão 000.000.000-00)
                    cpf_pattern = r"\d{3}\.\d{3}\.\d{3}\-\d{2}"
                    masked_text = re.sub(cpf_pattern, "[MASCARADO_CPF]", masked_text)
                
                elif rule.get("target_data") == "email":
                    # Simulação: Mascara Emails
                    email_pattern = r"[\w\.-]+@[\w\.-]+"
                    masked_text = re.sub(email_pattern, "[MASCARADO_EMAIL]", masked_text)
                    
                # Aqui você pode adicionar lógica para validar conformidade (ex: GDPR, HIPAA, LGPD)
                
        return masked_text

class PCCPolicyAgent:
    """
    Agente wrapper que contém o método 'apply_pcc_policies' esperado pelo llm_service.py.
    Ele lida com o ciclo de vida da sessão do DB internamente.
    """
    def apply_pcc_policies(self, raw_context: str, module_id: str = "llm_agent") -> str:
        """
        Busca as políticas ativas no DB e aplica o mascaramento ao texto bruto.
        """
        try:
            # 1. Cria e gerencia a sessão do DB (que PolicyService precisa)
            # Usa 'SessionLocal' para obter a sessão.
            with SessionLocal() as db:
                policy_service = PolicyService(db)
                
                # 2. Busca políticas ativas (podendo ser específica para o Agente LLM)
                policies = policy_service.get_active_policies(module_id=module_id)
                
                # 3. Aplica a lógica de mascaramento já existente
                return policy_service.apply_masking_policy(raw_context, policies)
        
        except Exception as e:
            # Em caso de falha de DB/Policy (e.g., DB offline), retorna o contexto bruto
            print(f"⚠️ [PCC Agent] Falha ao aplicar políticas de mascaramento: {e}. Retornando texto não mascarado.")
            return raw_context

# NOVO: Instância Singleton que llm_service.py está tentando importar.
# O llm_service.py fará a chamada 'policy_service.apply_pcc_policies(raw_context)', que agora é válida.
policy_service = PCCPolicyAgent()