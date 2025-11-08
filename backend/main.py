# backend/main.py (ATUALIZADO PARA ROTAS MODULARES E PRONTO PARA FUTURAS INCLUSÕES)
from fastapi import FastAPI
from datetime import datetime

# Importa o roteador de Contexto (já criado em api/context.py)
from backend.api import context, reserve, skill

# Mocka a importação dos módulos futuros para evitar erros de 'NameError'
# Estes módulos serão criados nas próximas tarefas.
class MockRouter:
    """Um objeto dummy para simular um APIRouter antes de ser criado."""
    def __init__(self, name):
        self.router = type('Router', (object,), {'prefix': f"/{name}", 'tags': [name]})
        
# Importações mockadas (manter comentadas até o arquivo ser criado)
# from backend.api import skill 
# from backend.api import reserve 

app = FastAPI(title="FlowMaster AI Backend Core", version="0.1.0")

# 1. Rota raiz (Status - MANTIDA)
@app.get("/")
def read_root():
    """Endpoint de teste para verificar se o backend está ativo."""
    return {"app_name": "FlowMaster AI", 
            "status": "online", 
            "timestamp": datetime.now().isoformat(),
            "docs": "/docs"}

# 2. Inclusão do Roteador de Contexto
app.include_router(context.router, prefix="/contexto", tags=["Contexto e Produtividade"])

# 3. Inclusão do Roteador Skill-Boost
app.include_router(skill.router, prefix="/skill", tags=["Desenvolvimento e Aprendizado"])

# 4. Inclusão do Roteador de Reserva Inteligente
app.include_router(reserve.router, prefix="/reserva", tags=["Infraestrutura e Logística"])