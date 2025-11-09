# backend/agent_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

# Modelo de dado que cada agente retornará para o frontend. 
# O frontend usará 'widget_type' para decidir como renderizar.
class AgentResult(ABC):
    """Modelo base para o resultado de um Agente. Deve ser serializável."""
    # Exemplo de tipo: 'card', 'detailed_card', 'full_section' (Item 3.2)
    widget_type: str 
    title: str
    icon_url: str = "default_icon.svg"
    data: Dict[str, Any] # O payload de dados para exibição (ex: resumo, sugestões)

# --- A Interface Abstrata de Plugin ---

class AbstractAgent(ABC):
    """
    Especificação da Interface de Agente (AIS). 
    TODO Agente novo deve herdar e implementar todos os métodos abstratos (@abstractmethod).
    """
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Retorna o ID único do agente (deve ser o mesmo usado no Config Service)."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadados de exibição para o frontend (nome, descrição, ícone).
        Usado na tela de configurações de usuário/admin.
        """
        pass

    @abstractmethod
    def process_request(self, user_id: int, input_data: Dict[str, Any]) -> List[AgentResult]:
        """
        O método principal de execução do Agente. Recebe os dados brutos/contexto
        e retorna uma lista de resultados formatados para o Frontend.
        """
        pass

    @abstractmethod
    def register_routes(self, router) -> None:
        """
        Método usado para registrar endpoints específicos do agente no FastAPI.
        Ex: /skill/suggestions, /reserva/suggestion
        """
        pass