# backend/Dockerfile - Contêiner para o Serviço de Backend FlowMaster AI

# Estágio 1: Build (Instalação de dependências e preparação)
# Usamos a imagem Python mais leve, mas com base no Linux Debian para estabilidade
FROM python:3.11-slim-buster AS builder

# Variáveis de ambiente
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Cria o diretório de trabalho
WORKDIR $APP_HOME

# Copia apenas o arquivo de dependências
COPY requirements.txt .

# Instala as dependências de forma segura, com cache desativado para imagem final limpa
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 2: Runtime (Imagem final mais leve)
FROM python:3.11-slim-buster AS final

ENV APP_HOME /app
WORKDIR $APP_HOME

# Copia as dependências instaladas do estágio 'builder'
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia o código da aplicação para o contêiner
COPY . .

# Comando de execução: Uvicorn rodando a aplicação 'main' no módulo 'backend'
# O argumento '--host 0.0.0.0' é necessário para expor a porta dentro do contêiner
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]