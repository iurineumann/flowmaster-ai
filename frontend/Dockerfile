# frontend/Dockerfile - Contêiner para o Serviço de Frontend FlowMaster AI

# Estágio 1: Build (Instalação e Compilação)
FROM node:18-alpine AS builder

WORKDIR /app

# Copia os arquivos de configuração do Node
COPY package.json package-lock.json ./

# Instala as dependências
RUN npm install

# Copia o código da aplicação
COPY . .

# Executa o Build (tsc e vite build), que gera o diretório 'dist'
RUN npm run build

# Estágio 2: Runtime (Imagem NGINX para servir arquivos estáticos)
FROM nginx:alpine AS final

# Copia os arquivos de build do estágio anterior para o diretório de serviço do NGINX
# O 'dist' contém o index.html e os assets compilados
COPY --from=builder /app/dist /usr/share/nginx/html

# A porta 80 é a porta padrão do NGINX para HTTP
EXPOSE 80

# O comando padrão do NGINX já é iniciar o servidor
CMD ["nginx", "-g", "daemon off;"]