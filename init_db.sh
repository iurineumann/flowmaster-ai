#!/bin/bash
# init_db.sh: Script que aguarda o DB, executa migrações e popula dados.

echo "⏳ Aguardando o PostgreSQL iniciar..."
# Ativa o venv
source /app/.venv/bin/activate

# 1. Espera o serviço 'db' estar disponível
python -c "
import socket
import time
host = '${DB_HOST:-db}'
port = 5432
print(f'Aguardando {host}:{port}...')
while True:
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        break
    except socket.error:
        print('PostgreSQL não está pronto, esperando 1s...')
        time.sleep(1)
print('✅ PostgreSQL está pronto.')
"

# ✅ ETAPA DE MIGRAÇÃO (NOVO)
echo "🛠️ Executando migrações do Alembic (upgrade head)..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "❌ ERRO: Falha ao executar 'alembic upgrade head'."
    # Se falhar, o Gunicorn não deve iniciar
    exit 1 
fi

# 2. Executa o comando Python para popular dados
echo "🛠️ Executando população de dados (usuários e módulos)..."
python -c "
from backend.db.database import SessionLocal
from backend.services.config_repository import populate_initial_data, ensure_mock_user_exists
from sqlalchemy.exc import IntegrityError

try:
    db = SessionLocal()
    print('💡 [DB] Verificando e populando dados iniciais...')
    populate_initial_data(db) 
    ensure_mock_user_exists(db) 
    db.commit() 
    print('✅ [DB] População de dados concluída.')
except IntegrityError as e:
    db.rollback()
    print(f'⚠️ [DB] Dados já existiam ou houve erro de integridade: {e}. Ignorando.')
except Exception as e:
    db.rollback()
    print(f'❌ [DB] Erro FATAL na população: {e}')
    exit(1)
finally:
    db.close()
"

if [ $? -ne 0 ]; then
    echo "❌ ERRO: O script de população do DB falhou."
    exit 1
fi

echo "✅ Inicialização do DB concluída com sucesso."