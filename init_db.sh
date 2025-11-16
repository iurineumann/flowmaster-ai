#!/bin/bash
# init_db.sh: Script executado UMA VEZ para criar tabelas e popular dados.

echo "⏳ Aguardando o PostgreSQL iniciar..."
# Ativa o venv
source /app/.venv/bin/activate

# 1. Espera o serviço 'db' estar disponível
python -c "
import socket
import time
host = '${DB_HOST:-db}' # Usa a variável de ambiente ou 'db'
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

echo "🛠️ Executando criação de tabelas e população..."
# 2. Executa o comando Python para criar e popular
python -c "
from backend.db.database import create_db_and_tables, SessionLocal
from backend.services.config_repository import populate_initial_data, ensure_mock_user_exists
from sqlalchemy.exc import IntegrityError
import time

try:
    # 1. Cria as tabelas
    create_db_and_tables() 

    # 2. Popula os dados
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
    exit(1) # Falha o script se a população falhar
finally:
    db.close()
"

if [ $? -ne 0 ]; then
    echo "❌ ERRO: O script de inicialização do DB falhou."
    exit 1
fi

echo "✅ Inicialização do DB concluída com sucesso."