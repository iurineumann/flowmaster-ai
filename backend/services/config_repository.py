# backend/services/config_repository.py

from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import models 
from ..api.schemas import SystemModuleDetail 

class ConfigRepository:
    """
    Repositório para operações de persistência relacionadas à Configuração e Usuário.
    """

    def __init__(self, db: Session):
        self.db = db

    # --- Módulos ---
        
    def get_all_system_modules(self) -> List[models.SystemModuleDetailModel]:
        return self.db.query(models.SystemModuleDetailModel).all()

    def create_system_module(self, module: SystemModuleDetail) -> models.SystemModuleDetailModel:
        db_module = models.SystemModuleDetailModel(**module.model_dump())
        self.db.add(db_module)
        self.db.commit()
        self.db.refresh(db_module)
        return db_module

    # --- Configuração Usuário ---

    def get_user_config(self, user_id: int) -> Optional[models.UserConfigModel]:
        return self.db.query(models.UserConfigModel).filter(models.UserConfigModel.user_id == user_id).first()

    def get_user_module_preferences(self, user_id: int) -> List[models.UserModulePreferenceModel]:
        preferences = self.db.query(models.UserModulePreferenceModel).filter(
            models.UserModulePreferenceModel.user_id == user_id
        ).all()
        
        if preferences:
            return preferences
        return self._create_default_user_preferences(user_id)

    def update_user_module_preferences(self, user_id: int, preferences: list) -> List[models.UserModulePreferenceModel]:
        # ... (Lógica de update mantida, simplificada aqui para brevidade, mas deve existir)
        existing = {p.module_id: p for p in self.get_user_module_preferences(user_id)}
        for pref in preferences:
            if pref.module_id in existing:
                existing[pref.module_id].is_active = pref.is_active
                existing[pref.module_id].display_order = pref.display_order
                self.db.add(existing[pref.module_id])
            else:
                new_pref = models.UserModulePreferenceModel(
                    user_id=user_id, module_id=pref.module_id, 
                    is_active=pref.is_active, display_order=pref.display_order
                )
                self.db.add(new_pref)
        self.db.commit()
        return self.get_user_module_preferences(user_id)

    def _create_default_user_preferences(self, user_id: int) -> List[models.UserModulePreferenceModel]:
        system_modules = self.get_all_system_modules()
        new_preferences = []
        for i, module in enumerate(system_modules):
            new_pref = models.UserModulePreferenceModel(
                user_id=user_id, module_id=module.id, is_active=True, display_order=i+1
            )
            self.db.add(new_pref)
            new_preferences.append(new_pref)
        self.db.commit()
        return new_preferences
        
    def ensure_user_config_exists(self, user_id: int):
        if self.get_user_config(user_id) is None:
            db_user_config = models.UserConfigModel(user_id=user_id, theme="dark")
            self.db.add(db_user_config)
            self.db.commit()

    # --- Usuário ---

    def get_user_by_username(self, username: str) -> Optional[models.UserModel]:
        return self.db.query(models.UserModel).filter(models.UserModel.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[models.UserModel]:
        return self.db.query(models.UserModel).filter(models.UserModel.id == user_id).first()

    def create_user(self, username: str, hashed_password: str, user_id: int = None, email: str = None, full_name: str = None, is_active: bool = True) -> models.UserModel:
        """Cria um novo usuário. Aceita ID opcional (para mock)."""
        db_user = models.UserModel(
            username=username, 
            email=email if email else username, # Fallback email = username
            hashed_password=hashed_password, 
            full_name=full_name,
            is_active=is_active
        )
        if user_id:
            db_user.id = user_id # Força ID se fornecido (útil para o mock devuser=123)
            
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

# --- Funções de Inicialização ---

def populate_initial_data(db: Session):
    repo = ConfigRepository(db)
    if repo.get_all_system_modules():
        return

    print("🛠️ [DB] Populando dados iniciais...")
    SYSTEM_MODULES_INITIAL = [
        SystemModuleDetail(id="context_agent", name="Contexto e Foco", description="Agrega comunicações e define o foco de trabalho.", api_endpoint="/contexto/agregado", grid_column_span=2),
        SystemModuleDetail(id="skill_agent", name="Sugestão de Skills", description="Sugere habilidades baseadas no foco.", api_endpoint="/skill/sugestoes", grid_column_span=1),
        SystemModuleDetail(id="reserve_agent", name="Reserva de Recursos", description="Sugere salas de foco.", api_endpoint="/reserva/sugestao", grid_column_span=1),
        SystemModuleDetail(id="meeting_agent", name="Sugestão de Reunião", description="Sugere pautas e horários.", api_endpoint="/meeting/sugestao", grid_column_span=1),
        SystemModuleDetail(id="chat_agent", name="Chat Contextual", description="Chat com IA sobre o contexto.", api_endpoint="/chat/query", grid_column_span=2),
    ]
    for module in SYSTEM_MODULES_INITIAL:
        repo.create_system_module(module)

def ensure_mock_user_exists(db: Session):
    repo = ConfigRepository(db)
    if repo.get_user_by_username("devuser"):
        return

    print("🛠️ [DB] Criando usuário 'devuser'...")
    from ..utils.security import get_password_hash
    
    hashed = get_password_hash("devpass")
    user = repo.create_user(
        username="devuser", 
        email="devuser@flowmaster.ai",
        hashed_password=hashed, 
        user_id=123 # ID Fixo para testes
    )
    
    repo.ensure_user_config_exists(user.id)
    repo.get_user_module_preferences(user.id) # Cria prefs default