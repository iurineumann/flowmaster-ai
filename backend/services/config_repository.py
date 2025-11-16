# backend/services/config_repository.py

from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import models 
from ..api.schemas import SystemModuleDetail, UserModulePreference

class ConfigRepository:
    """
    Repositório para operações de persistência relacionadas à Configuração.
    """

    def __init__(self, db: Session):
        self.db = db

    # --- Operações de Módulos do Sistema ---
        
    def get_all_system_modules(self) -> List[models.SystemModuleDetailModel]:
        return self.db.query(models.SystemModuleDetailModel).all()

    def create_system_module(self, module: SystemModuleDetail) -> models.SystemModuleDetailModel:
        db_module = models.SystemModuleDetailModel(**module.model_dump())
        self.db.add(db_module)
        self.db.commit()
        self.db.refresh(db_module)
        return db_module

    # --- Operações de Configuração do Usuário ---

    def get_user_config(self, user_id: int) -> Optional[models.UserConfigModel]:
        return self.db.query(models.UserConfigModel).filter(models.UserConfigModel.user_id == user_id).first()

    def get_user_module_preferences(self, user_id: int) -> List[models.UserModulePreferenceModel]:
        preferences = self.db.query(models.UserModulePreferenceModel).filter(
            models.UserModulePreferenceModel.user_id == user_id
        ).all()
        
        if preferences:
            return preferences
            
        return self._create_default_user_preferences(user_id)

    def update_user_module_preferences(self, user_id: int, preferences: List[UserModulePreference]) -> List[models.UserModulePreferenceModel]:
        """Atualiza em lote as preferências de módulo (is_active e display_order)."""
        
        existing_prefs_query = self.db.query(models.UserModulePreferenceModel).filter(
            models.UserModulePreferenceModel.user_id == user_id
        )
        existing_prefs = {p.module_id: p for p in existing_prefs_query.all()}
        
        for pref_data in preferences:
            module_id = pref_data.module_id
            
            if module_id in existing_prefs:
                db_pref = existing_prefs[module_id]
                db_pref.is_active = pref_data.is_active
                db_pref.display_order = pref_data.display_order
                self.db.add(db_pref) 
            else:
                db_pref = models.UserModulePreferenceModel(
                    user_id=user_id,
                    module_id=module_id,
                    is_active=pref_data.is_active,
                    display_order=pref_data.display_order
                )
                self.db.add(db_pref)

        self.db.commit()
        
        return self.get_user_module_preferences(user_id)

    def _create_default_user_preferences(self, user_id: int) -> List[models.UserModulePreferenceModel]:
        system_modules = self.get_all_system_modules()
        
        next_order = 10
        
        new_preferences = []
        for module in system_modules:
            new_pref = models.UserModulePreferenceModel(
                user_id=user_id,
                module_id=module.id,
                is_active=True,
                display_order=next_order
            )
            self.db.add(new_pref)
            new_preferences.append(new_pref)
            next_order += 10 
            
        self.db.commit()
        for pref in new_preferences:
            self.db.refresh(pref)
            
        return new_preferences
        
    def ensure_user_config_exists(self, user_id: int):
        if self.get_user_config(user_id) is None:
            db_user_config = models.UserConfigModel(user_id=user_id, theme="dark")
            self.db.add(db_user_config)
            self.db.commit()
            
        self.get_user_module_preferences(user_id=user_id)

    def get_user_by_username(self, username: str) -> Optional[models.UserModel]:
        return self.db.query(models.UserModel).filter(models.UserModel.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[models.UserModel]:
        return self.db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    
    def count_all_users(self) -> int:
        return self.db.query(models.UserModel).count()

    def create_user(self, username: str, hashed_password: str, user_id: int = None, email: str = None, full_name: str = None, is_active: bool = True) -> models.UserModel:
        db_user = models.UserModel(
            username=username, 
            email=email if email else username,
            hashed_password=hashed_password, 
            full_name=full_name,
            is_active=is_active
        )
        if user_id:
            db_user.id = user_id
            
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

# --- Funções de Inicialização ---

def populate_initial_data(db: Session):
    repo = ConfigRepository(db)
    
    if repo.get_all_system_modules():
        print("💡 [DB] Dados iniciais de módulos já existem.")
        return

    print("🛠️ [DB] Populando dados iniciais de módulos...")
    
    SYSTEM_MODULES_INITIAL: List[SystemModuleDetail] = [
        SystemModuleDetail(id="context_agent", name="Contexto e Foco", description="Agrega comunicações e define o foco de trabalho atual.", api_endpoint="/contexto/agregado", grid_column_span=2),
        SystemModuleDetail(id="skill_agent", name="Sugestão de Skills", description="Sugere habilidades de aprendizado com base no foco crítico.", api_endpoint="/skill/sugestoes", grid_column_span=1),
        SystemModuleDetail(id="reserve_agent", name="Reserva de Recursos", description="Sugere a reserva de salas de foco para momentos críticos.", api_endpoint="/reserva/sugestao", grid_column_span=1),
        SystemModuleDetail(id="meeting_agent", name="Sugestão de Reunião", description="Sugere pautas e horários.", api_endpoint="/meeting/sugestao", grid_column_span=1),
        SystemModuleDetail(id="chat_agent", name="Chat Contextual", description="Chat com IA sobre o contexto.", api_endpoint="/chat/query", grid_column_span=2),
    ]

    for module in SYSTEM_MODULES_INITIAL:
        repo.create_system_module(module)

def ensure_mock_user_exists(db: Session):
    repo = ConfigRepository(db)
    
    if repo.get_user_by_username("devuser"):
        print("💡 [DB] Usuário de desenvolvimento 'devuser' já existe.")
        return

    print("🛠️ [DB] Criando usuário de desenvolvimento 'devuser'...")
    
    # Importação local para quebrar o ciclo de importação
    from ..utils.security import get_password_hash
    
    hashed_password = get_password_hash("devpass") 
    user = repo.create_user(
        username="devuser", 
        email="devuser@flowmaster.ai",
        hashed_password=hashed_password, 
        user_id=123
    )
    
    repo.ensure_user_config_exists(user.id)