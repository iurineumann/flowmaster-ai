# backend/services/config_repository.py (CORRIGIDO - Sem Circular Import)

from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import models 
# NOVO: Importa Pydantic Schemas do novo módulo de schemas, resolvendo o problema:
from ..api.schemas import SystemModuleDetail 
#from ..utils.security import get_password_hash

class ConfigRepository:
    """
    Repositório para operações de persistência relacionadas à Configuração.
    """

    def __init__(self, db: Session):
        """Injeta a sessão do SQLAlchemy."""
        self.db = db

    # --- Operações de Módulos do Sistema ---
        
    def get_all_system_modules(self) -> List[models.SystemModuleDetailModel]:
        """Retorna todos os detalhes dos módulos globais."""
        return self.db.query(models.SystemModuleDetailModel).all()

    def create_system_module(self, module: SystemModuleDetail) -> models.SystemModuleDetailModel:
        """Cria um novo módulo (usado para popular o DB)."""
        db_module = models.SystemModuleDetailModel(**module.model_dump())
        self.db.add(db_module)
        self.db.commit()
        self.db.refresh(db_module)
        return db_module

    # --- Operações de Configuração do Usuário ---

    def get_user_config(self, user_id: int) -> Optional[models.UserConfigModel]:
        """Busca a configuração geral do usuário (tema)."""
        return self.db.query(models.UserConfigModel).filter(models.UserConfigModel.user_id == user_id).first()

    def get_user_module_preferences(self, user_id: int) -> List[models.UserModulePreferenceModel]:
        """
        Busca as preferências de módulos do usuário. 
        Se não existirem, cria as preferências padrão a partir dos módulos globais.
        """
        # 1. Busca as preferências existentes
        preferences = self.db.query(models.UserModulePreferenceModel).filter(
            models.UserModulePreferenceModel.user_id == user_id
        ).all()
        
        if preferences:
            return preferences
            
        # 2. Se não houver, cria as preferências padrão
        return self._create_default_user_preferences(user_id)


    def _create_default_user_preferences(self, user_id: int) -> List[models.UserModulePreferenceModel]:
        """Cria preferências padrão para um novo usuário."""
        system_modules = self.get_all_system_modules()
        
        # Pega a ordem máxima atual (se houver) ou começa em 10
        max_order = self.db.query(models.UserModulePreferenceModel.display_order)\
                          .filter(models.UserModulePreferenceModel.user_id == user_id)\
                          .order_by(models.UserModulePreferenceModel.display_order.desc())\
                          .first()
        
        next_order = (max_order[0] + 1) if max_order else 10
        
        new_preferences = []
        for module in system_modules:
            new_pref = models.UserModulePreferenceModel(
                user_id=user_id,
                module_id=module.id,
                is_active=True, # Por padrão, ativo
                display_order=next_order
            )
            self.db.add(new_pref)
            new_preferences.append(new_pref)
            next_order += 10 # Incrementa para o próximo
            
        self.db.commit()
        for pref in new_preferences:
            self.db.refresh(pref)
            
        return new_preferences
        
    def ensure_user_config_exists(self, user_id: int):
        """Garante que o registro UserConfigModel exista para o usuário."""
        if self.get_user_config(user_id) is None:
            db_user_config = models.UserConfigModel(user_id=user_id, theme="dark")
            self.db.add(db_user_config)
            self.db.commit()
            
        # As preferências de módulo são criadas na `get_user_module_preferences`
        # se ainda não existirem.

    # NOVO: Adiciona a função para buscar usuário por nome de usuário (necessário para o mock)
    def get_user_by_username(self, username: str) -> Optional[models.UserModel]:
        """Busca um usuário pelo nome de usuário."""
        return self.db.query(models.UserModel).filter(models.UserModel.username == username).first()

    # NOVO: Adiciona a função para criar um novo usuário (necessário para o mock)
    def create_user(self, username: str, hashed_password: str) -> models.UserModel:
        """Cria um novo usuário."""
        db_user = models.UserModel(username=username, hashed_password=hashed_password, is_active=True)
        self.db.add(db_user)
        self.db.flush() # flush() para obter o ID antes do commit, se necessário
        return db_user

# --- Funções de Inicialização e População (Mock) ---

def populate_initial_data(db: Session):
    """Popula o DB com os dados iniciais dos módulos do sistema."""
    repo = ConfigRepository(db)
    
    # Evita repopular se já houver dados
    if repo.get_all_system_modules():
        print("💡 [DB] Dados iniciais de módulos já existem.")
        return

    print("🛠️ [DB] Populando dados iniciais de módulos...")
    
    SYSTEM_MODULES_INITIAL: List[SystemModuleDetail] = [
        SystemModuleDetail(id="context_agent", name="Contexto e Foco", description="Agrega comunicações e define o foco de trabalho atual.", api_endpoint="/contexto/agregado", grid_column_span=2),
        SystemModuleDetail(id="skill_agent", name="Sugestão de Skills", description="Sugere habilidades de aprendizado com base no foco crítico.", api_endpoint="/skill/sugestoes", grid_column_span=1),
        SystemModuleDetail(id="reserve_agent", name="Reserva de Recursos", description="Sugere a reserva de salas de foco para momentos críticos.", api_endpoint="/reserva/sugestao", grid_column_span=1),
        SystemModuleDetail(id="project_health", name="Saúde do Projeto", description="Monitora a saúde geral de projetos (Atualmente inativo).", api_endpoint="/projeto/saude", grid_column_span=2),
    ]

    for module in SYSTEM_MODULES_INITIAL:
        repo.create_system_module(module)
    
    # Note: O db.commit() será chamado na função create_db_and_tables

# NOVO: Função para garantir que o usuário de teste exista
def ensure_mock_user_exists(db: Session):
    """Cria o usuário de teste ('devuser') se ele não existir."""
    repo = ConfigRepository(db)
    
    # Verifica se o usuário já existe
    if repo.get_user_by_username("devuser"):
        print("💡 [DB] Usuário de desenvolvimento 'devuser' já existe.")
        return

    print("🛠️ [DB] Criando usuário de desenvolvimento 'devuser'...")
    
    from ..utils.security import get_password_hash
    # Cria o usuário
    hashed_password = get_password_hash("devpass") 
    user = repo.create_user(username="devuser", hashed_password=hashed_password)
    
    # Cria a configuração inicial do usuário (tema 'dark')
    db_config = models.UserConfigModel(user_id=user.id, theme="dark")
    db.add(db_config)
    
    # Cria as preferências iniciais de módulo para este novo usuário
    default_preferences = [
        models.UserModulePreferenceModel(user_id=user.id, module_id="context_agent", is_active=True, display_order=1),
        models.UserModulePreferenceModel(user_id=user.id, module_id="skill_agent", is_active=True, display_order=2),
        # Adicione outras preferências padrão se desejar...
    ]
    db.add_all(default_preferences)

# Note: O db.commit() será chamado na função create_db_and_tables