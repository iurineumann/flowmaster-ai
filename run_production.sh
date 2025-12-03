#!/bin/bash
# run_production.sh

# Ativa o modo de erro estrito
set -e

echo "========================================="
echo "🚀 FlowMaster AI - Startup de Produção"
echo "========================================="

# 1. Configuração do Ambiente
VENV_PATH="/app/.venv"
export PATH="$VENV_PATH/bin:$PATH"

# 2. Carrega variáveis (opcional se já vierem do Docker)
if [ -f ".env" ]; then
    echo "💡 Carregando variáveis do .env"
    export $(grep -v '^#' .env | xargs)
fi

# 3. Espera o Banco de Dados estar pronto (Loop simples)
echo "⏳ Aguardando o PostgreSQL iniciar..."
until python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('db', 5432))" 2>/dev/null; do
  echo "   ...aguardando db:5432..."
  sleep 2
done
echo "✅ PostgreSQL está pronto."

# 4. Executa Migrações do Banco de Dados (CRÍTICO)
echo "🛠️ Executando migrações do Alembic (upgrade head)..."
alembic upgrade head

# 5. Popula dados iniciais (se necessário)
echo "🛠️ Executando população de dados (usuários e módulos)..."
python -m backend.initial_data_mock

# 6. Inicia o Servidor
WORKERS=${GUNICORN_WORKERS:-5}
TIMEOUT=${GUNICORN_TIMEOUT:-120}

echo "🚀 Iniciando Gunicorn com $WORKERS workers..."
exec gunicorn backend.main:app \
  --workers $WORKERS \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout $TIMEOUT \
  --log-level info