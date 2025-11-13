#!/bin/bash
# run_production.sh
# Script que garante a criação e configuração do virtual environment antes de rodar o Gunicorn.

VENV_NAME=".venv"
VENV_PATH="./$VENV_NAME"
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
REQUIREMENTS_FILE="./backend/requirements.txt"

echo "========================================="
echo "🚀 FlowMaster AI - Startup de Produção"
echo "========================================="

# 1. Checa e Cria/Configura o Ambiente Virtual
if [ ! -d "$VENV_PATH" ]; then
    echo "⚙️ Ambiente virtual '$VENV_NAME' não encontrado. Criando..."
    python3 -m venv "$VENV_PATH"

    if [ $? -ne 0 ]; then
        echo "❌ ERRO: Falha ao criar o ambiente virtual. Certifique-se de que 'python3 -m venv' está disponível."
        exit 1
    fi
    
    echo "Ativando e instalando dependências..."
    source "$ACTIVATE_SCRIPT"

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo "❌ ERRO: Arquivo de requisitos não encontrado em '$REQUIREMENTS_FILE'. Abortando."
        exit 1
    fi

    # Instala as dependências, incluindo uvicorn
    pip install -r "$REQUIREMENTS_FILE"
    
    # Adiciona a mensagem de que o ambiente foi configurado
    echo "✅ Configuração inicial do ambiente concluída."
else
    echo "✅ Ambiente virtual '$VENV_NAME' já existe."
    source "$ACTIVATE_SCRIPT"
fi


# 2. Carrega as variáveis de ambiente do arquivo .env
if [ -f ".env" ]; then
    echo "💡 Carregando variáveis do .env"
    # Exporta variáveis de ambiente, ignorando comentários
    export $(grep -v '^#' .env | xargs)
fi

# 3. Determina o número de workers
WORKERS=$(($(nproc) * 2 + 1))

echo "⏳ Iniciando servidor Gunicorn/Uvicorn com $WORKERS workers na porta 8000..."

# 4. Executa Gunicorn
gunicorn backend.main:app \
  --workers $WORKERS \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --log-level info

# O ambiente virtual permanece ativo na sub-shell até a finalização do Gunicorn