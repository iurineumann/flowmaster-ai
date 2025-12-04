# backend/services/config_repository.py

from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import models 
from ..api.schemas import SystemModuleDetail, UserModulePreference

class ConfigRepository:
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
        ).order_by(models.UserModulePreferenceModel.display_order).all()
        
        if preferences:
            return preferences
            
        return self._create_default_user_preferences(user_id)

    def update_user_module_preferences(self, user_id: int, preferences: List[UserModulePreference]) -> List[models.UserModulePreferenceModel]:
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
        
        self.get_user_module_preferences(user_id) # Garante que as prefs tbm existam

        # --- DEV HELPER: Adiciona uma conexão ADO padrão para facilitar testes quando
        # estiver em ambiente de desenvolvimento e o usuário não tiver conexões.
        try:
            import os
            if os.environ.get('DEV_AUTO_ADD_ADO', 'false').lower() == 'true':
                connections = self.get_ado_connections(user_id)
                if not connections:
                    default_org = os.environ.get('DEV_ADO_ORG_URL', 'https://dev.azure.com/sample-org')
                    print(f"🛠️ [ConfigRepo] Adicionando conexão ADO padrão para o usuário {user_id}: {default_org}")
                    try:
                        self.create_ado_connection(user_id, default_org)
                        # opcional: criar um projeto de exemplo
                        # self.create_ado_project(connection_id, 'SampleProject')
                    except Exception as e:
                        print(f"⚠️ [ConfigRepo] Falha ao criar conexão ADO padrão: {e}")
        except Exception as e:
            print(f"⚠️ [ConfigRepo] Erro ao verificar/instalar conexão ADO padrão: {e}")

    # --- Usuário ---

    def get_user_by_username(self, username: str) -> Optional[models.UserModel]:
        return self.db.query(models.UserModel).filter(
            (models.UserModel.username == username) | (models.UserModel.email == username)
        ).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[models.UserModel]:
        return self.db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    
    def count_all_users(self) -> int:
        return self.db.query(models.UserModel).count()

    def create_user(
        self, username: str, hashed_password: str, 
        user_id: Optional[int] = None, 
        email: Optional[str] = None, 
        full_name: Optional[str] = None, 
        is_active: bool = True,
        microsoft_id: Optional[str] = None
    ) -> models.UserModel:
        
        db_user = models.UserModel(
            username=username, 
            email=email if email else username,
            microsoft_id=microsoft_id,
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

    # --- NOVOS MÉTODOS (ADO Config) ---

    def get_ado_connections(self, user_id: int):
        return self.db.query(models.UserAdoConnection).filter(models.UserAdoConnection.user_id == user_id).all()
    
    def add_ado_connection(self, user_id: int, org_url: str, personal_access_token: str = None):
        existing = self.db.query(models.UserAdoConnection).filter(
            models.UserAdoConnection.user_id == user_id,
            models.UserAdoConnection.organization_url == org_url
        ).first()
        
        if existing:
            # Se já existe, atualiza o token se fornecido, senão apenas ativa
            if personal_access_token:
                existing.personal_access_token = personal_access_token
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            return existing
            
        conn = models.UserAdoConnection(
            user_id=user_id, 
            organization_url=org_url,
            personal_access_token=personal_access_token
        )
        self.db.add(conn)
        self.db.commit()
        self.db.refresh(conn)
        return conn

    def get_ado_projects_for_connection(self, connection_id: int):
        # Retorna vazio por enquanto, expansível futuramente
        return []

    # ✅ NOVO: Método para DELETAR conexão
    def delete_ado_connection(self, user_id: int, connection_id: int) -> bool:
        conn = self.db.query(models.UserAdoConnection).filter(
            models.UserAdoConnection.id == connection_id, 
            models.UserAdoConnection.user_id == user_id
        ).first()
        
        if conn:
            self.db.delete(conn)
            self.db.commit()
            return True
        return False

    # ✅ NOVO: Método para ATUALIZAR PAT
    def update_ado_connection_pat(self, user_id: int, connection_id: int, encrypted_pat: str):
        conn = self.db.query(models.UserAdoConnection).filter(
            models.UserAdoConnection.id == connection_id, 
            models.UserAdoConnection.user_id == user_id
        ).first()
        
        if conn:
            conn.personal_access_token = encrypted_pat
            self.db.commit()
            self.db.refresh(conn)
            return conn
        return None

    def get_ado_connection_by_id(self, connection_id: int) -> Optional[models.UserAdoConnection]:
        return self.db.query(models.UserAdoConnection).filter(models.UserAdoConnection.id == connection_id).first()

    def get_ado_projects_for_connection(self, connection_id: int) -> List[models.AdoProjectConfig]:
        """Lista todos os projetos ativos para uma conexão ADO."""
        return self.db.query(models.AdoProjectConfig)\
            .filter(models.AdoProjectConfig.connection_id == connection_id, models.AdoProjectConfig.is_active == True)\
            .all()

    def add_ado_connection(self, user_id: int, org_url: str, personal_access_token: str = None):
        # ... verificações existentes ...
        conn = models.UserAdoConnection(
            user_id=user_id, 
            organization_url=org_url,
            personal_access_token=personal_access_token # ✅ Salva o token
        )
        self.db.add(conn)
        self.db.commit()
        self.db.refresh(conn)
        return conn
    
    def create_ado_project(self, connection_id: int, project_name: str) -> models.AdoProjectConfig:
        """Adiciona um novo projeto monitorado a uma conexão."""
        db_proj = models.AdoProjectConfig(connection_id=connection_id, project_name=project_name)
        self.db.add(db_proj)
        self.db.commit()
        self.db.refresh(db_proj)
        return db_proj

    async def sync_ado_projects_for_connection(self, connection_id: int, organization_url: str, access_token: str) -> List[models.AdoProjectConfig]:
        """
        Busca projetos na organização ADO e sincroniza com o banco:
         - Cria projetos que não existem
         - Marca como inativos projetos que foram removidos

        Retorna a lista atualizada de projetos para a connection_id.
        """
        from ..integrations.ado_client import ADOClient

        client = None
        try:
            client = ADOClient(access_token, organization_url)
            projects = await client.get_projects()
            fetched_names = {p.get('name') for p in projects if p.get('name')}

            # Carrega projetos existentes
            existing = self.db.query(models.AdoProjectConfig).filter(models.AdoProjectConfig.connection_id == connection_id).all()
            existing_names = {p.project_name for p in existing}

            # Criar novos
            for name in fetched_names - existing_names:
                try:
                    self.create_ado_project(connection_id, name)
                    print(f"✅ [ConfigRepo] Projeto ADO criado: {name}")
                except Exception as e:
                    print(f"⚠️ [ConfigRepo] Falha ao criar projeto {name}: {e}")

            # Marcar como inativo projetos removidos upstream
            to_deactivate = [p for p in existing if p.project_name not in fetched_names]
            for p in to_deactivate:
                p.is_active = False
                self.db.add(p)

            self.db.commit()

            # Retornar lista atualizada
            updated = self.get_ado_projects_for_connection(connection_id)
            return updated

        except Exception as e:
            print(f"❌ [ConfigRepo] Erro ao sincronizar projetos ADO para connection {connection_id}: {e}")
            raise
        finally:
            if client:
                try:
                    await client.close()
                except Exception:
                    pass

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
        # ✅ NOVO AGENTE ADO
        SystemModuleDetail(id="ado_agent", name="Azure DevOps (Work Items)", description="Exibe seus Work Items e Bugs do ADO.", api_endpoint="/ado/work_items", grid_column_span=2),
    ]

    for module in SYSTEM_MODULES_INITIAL:
        repo.create_system_module(module)

def ensure_mock_user_exists(db: Session):
    repo = ConfigRepository(db)
    
    if repo.get_user_by_username("devuser"):
        print("💡 [DB] Usuário de desenvolvimento 'devuser' já existe.")
        return

    print("🛠️ [DB] Criando usuário de desenvolvimento 'devuser'...")
    
    from ..utils.security import get_password_hash
    
    hashed_password = get_password_hash("devpass") 
    user = repo.create_user(
        username="devuser", 
        email="devuser@flowmaster.ai",
        hashed_password=hashed_password, 
        user_id=123 # ID Fixo para testes
    )
    
    repo.ensure_user_config_exists(user.id)