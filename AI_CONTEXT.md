# PROJECT: FLOWMASTER AI - CONTEXTO MESTRE

## 1. Visão do Produto
Sistema de produtividade "AI First" para gestão de trabalho híbrido na T2M, focado em eliminar o "context switching".
**Stack:** Python (FastAPI), React (Vite/TS), PostgreSQL, Redis, Docker Compose.
**Core AI:** LLM Local (Ollama/Mistral) + Vector DB (ChromaDB) + RAG.
**Arquitetura:** Modular (Plugins), Assíncrona, Orientada a Eventos.

## 2. Arquitetura Atual & Decisões Técnicas (IMUTÁVEL)
* **Backend:** FastAPI totalmente assíncrono (`async/await`).
* **Segurança:**
    * JWT (`backend/utils/security.py`) validando tokens internos e do Entra ID.
    * **PCC Agent:** Todo prompt para LLM passa por `PolicyService` para mascaramento de PII.
* **Cache:** Multi-camadas (`backend/utils/multi_layer_cache.py`) usando Memória (L1) + Redis (L2).
* **Comunicação:**
    * REST para Configuração e Dados Iniciais.
    * WebSockets (`/notifications/ws`) para alertas críticos (urgency >= 90).
* **Integrações:**
    * Microsoft Graph (via `GraphRepository` com fallback robusto para Mock).
    * LLM Customizada (via `LLMService` apontando para `ctb.qualbet.top:11434`).

## 3. Contratos de Dados (API Response Schemas)
O Frontend DEVE esperar e tipar estas estruturas exatas:

### A. Configuração (`/api/v1/config/user`)
```typescript
interface UserConfig {
  user_id: number;
  theme: 'light' | 'dark';
  modules: {
    module_id: string; // ex: 'context_agent', 'skill_agent'
    is_active: boolean;
    display_order: number;
  }[];
}
````

### B. Contexto & Foco (`/api/v1/contexto/agregado`)

```typescript
interface ContextAgentData {
  user_id: number;
  foco_critico: string; // Tag do projeto (ex: 'CLIENTE_X')
  foco_detalhe: string; // Texto completo do problema
  resumo_llm: {
    focus_title: string;
    summary_analysis: string;
    urgency_score: number;
    technical_tags: string[];
  };
  sugestoes_conhecimento: {
    title: string;
    summary: string;
    score: number;
    link: string;
  }[];
}
```

### C. Skills (`/api/v1/skill/sugestoes`)

```typescript
interface SkillAgentData {
  suggestions: {
    title: string;
    relevance_score: number;
    link?: string;
  }[];
}
```

### D. Reserva (`/api/v1/reserva/sugestao`)

```typescript
interface ReserveAgentData {
  is_suggested: boolean;
  resource_name: string;
  time_slot: string;
  reason: string;
  link_to_map?: string;
}
```

## 4\. Regras de Desenvolvimento (Para o Agente de Código)

1.  **SOLID & DRY:** Nunca duplique lógica de busca de dados. Use `ContextDataService` no backend.
2.  **Tipagem:** Python deve usar Pydantic/TypeHints. Frontend **OBRIGATORIAMENTE** TypeScript estrito (`types.ts`).
3.  **Frontend:**
      * Use `useEffect` e `useState` para chamadas de API.
      * Use `useMemo` para cálculos de layout.
      * Use variáveis CSS (`var(--color-t2m-primary)`) para cores.
4.  **Docker:** O ambiente roda via `docker-compose up --build`. Backend usa Gunicorn.

## 5\. BACKLOG DE IMPLEMENTAÇÃO (Missões para o Jules)

1.  **[Frontend] Componentes de Cards:** Criar `ContextCard.tsx`, `SkillCard.tsx` e `ReserveCard.tsx` em `frontend/src/agents/` consumindo as interfaces acima.
2.  **[Frontend] Dashboard Dinâmico:** Atualizar `App.tsx` (ou `Dashboard.tsx`) para importar e renderizar esses cards dinamicamente baseado na config do usuário.
3.  **[Frontend] Chat Interativo:** Criar componente `ChatWidget.tsx` flutuante ou fixo para consumir a rota `/api/v1/chat/query`.
4.  **[Backend] Endpoint Admin Stats:** Implementar lógica real para `/api/v1/admin/stats` lendo chaves do Redis.

## 6\. Comandos Úteis

  * Backend Rebuild: `docker-compose up -d --build backend`
  * Frontend Dev: `npm run dev` (na pasta frontend)
