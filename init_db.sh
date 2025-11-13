#!/bin/bash
# init_db.sh: Script executado UMA VEZ para criar tabelas e popular dados.

echo "⏳ Aguardando o PostgreSQL iniciar..."
# 1. Espera o serviço 'db' estar disponível (muda o 'db' para o nome do seu serviço se for diferente)
/app/.venv/bin/python -c "
import socket
import time
host = 'db'
port = 5432
while True:
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        break
    except socket.error:
        print('PostgreSQL não está pronto, esperando...')
        time.sleep(1)
print('✅ PostgreSQL está pronto.')
"

echo "🛠️ Executando criação de tabelas e população..."
# 2. Executa o comando Python para criar e popular (deve ser modificado para usar SessionLocal())
/app/.venv/bin/python -c "
from backend.db.database import create_db_and_tables, SessionLocal
from backend.services.config_repository import populate_initial_data, ensure_mock_user_exists
from sqlalchemy.exc import IntegrityError
import time

# Atraso para garantir que o Engine está conectado (opcional, mas seguro)
time.sleep(2) 

# 1. Cria as tabelas
create_db_and_tables() 

# 2. Popula os dados
db = SessionLocal()
try:
    print('💡 [DB] Verificando e populando dados iniciais...')
    populate_initial_data(db) 
    ensure_mock_user_exists(db) 
    db.commit() 
    print('✅ [DB] População de dados concluída.')
except IntegrityError:
    # Captura a exceção de chave duplicada e ignora, mas garante o rollback
    db.rollback()
    print('⚠️ [DB] Dados já existiam ou houve erro de concorrência. Ignorando e continuando.')
except Exception as e:
    db.rollback()
    print(f'❌ [DB] Erro FATAL na população: {e}')
finally:
    db.close()
"

if [ $? -ne 0 ]; then
    echo "❌ ERRO: O script de inicialização do DB falhou."
    exit 1
fi

echo "✅ Inicialização do DB concluída com sucesso."