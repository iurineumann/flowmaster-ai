// frontend/src/App.tsx
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import './App.css'; 

import { 
  ActiveModuleConfig, 
  DashboardConfig, 
  AgentPanelProps, 
  AgentData, 
  ContextAgentData, 
  SkillAgentData,
  ReserveAgentData,
  SystemModuleDetail,
  UserModulePreference
} from './types'; 

// Variáveis de Configuração
const USER_ID = 42;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api"; 


// --- Componente Agente (Componente Filha) ---
const AgentPanel: React.FC<AgentPanelProps> = ({ moduleConfig }) => {
  const [data, setData] = useState<AgentData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);
  
  // A função de fetch é memorizada para evitar recriação desnecessária (ESLint rule: exhaustive-deps)
  const fetchData = useCallback(async () => {
    const { name, api_endpoint_full } = moduleConfig;

    if (!api_endpoint_full) {
        setApiError(`API não configurada para o módulo ${name}.`);
        setLoading(false);
        return;
    }
    
    setLoading(true);
    setApiError(null);

    try {
      // Chamada tipada
      const response = await axios.get<AgentData>(api_endpoint_full);
      setData(response.data);
    } catch (e) {
      const error = e as AxiosError;
      console.error(`Erro ao buscar dados do agente ${name}:`, error);
      // Detalhe de erro claro para o usuário final
      setApiError(`Erro (${error.response?.status || 'network'}) ao buscar dados.`);
      setData(null); 
    } finally {
      setLoading(false);
    }
  }, [moduleConfig.api_endpoint_full, moduleConfig.name]); 

  // Executa o fetch na montagem e sempre que a função fetchData mudar (o que não deve acontecer)
  useEffect(() => {
    fetchData();
  }, [fetchData]); 

  
  // Sub-componente para renderizar o conteúdo específico
  const PanelContent: React.FC = () => {
    if (loading) return <p>Carregando dados de **{moduleConfig.name}**...</p>;
    if (apiError) return <p className="status offline">❌ {apiError}</p>;
    if (!data) return <p>Nenhum dado disponível.</p>;
    
    // O switch garante que a tipagem correta seja aplicada
    switch(moduleConfig.id) {
        case "context_agent":
            const contextData = data as ContextAgentData;
            // Validações básicas de objeto (TypeScript garante os campos)
            if (!contextData.foco_atual_titulo) return <p>Dados de contexto incompletos.</p>; 
            
            return (
                <div className="context-block">
                    <h4>Foco Atual: {contextData.foco_atual_titulo}</h4>
                    <p>Resumo IA: {contextData.resumo_ia}</p>
                    <p>Itens Agregados: **{contextData.numero_itens_agregados}**</p>
                    <p>Próxima Reunião: *{contextData.proxima_reuniao}*</p>
                </div>
            );
        case "skill_agent":
            const skillData = data as SkillAgentData;
             return (
                <div className="skill-boost-block">
                    {skillData.suggestions && skillData.suggestions.length > 0 ? (
                      skillData.suggestions.map((s, i) => (
                          <div key={i} className="suggestion-item">
                              <h4>{s.title}</h4>
                              <p>Score: <span className="score">{s.score}%</span></p>
                          </div>
                      ))
                    ) : (
                       <p>Nenhuma sugestão de skill encontrada.</p>
                    )}
                </div>
            );
        case "reserve_agent":
            const reserveData = data as ReserveAgentData;
            return (
                <div className="reserve-block">
                    <h4>Sugestão de Produtividade:</h4>
                    {/* A classe 'offline' pode ser usada para destacar a urgência (action_required) */}
                    <p className={reserveData.action_required ? 'status offline' : ''}>
                        {reserveData.suggestion}
                    </p>
                    {reserveData.link_to_map && (
                        <a href={reserveData.link_to_map} target="_blank" rel="noopener noreferrer">
                            <button>Ver Mapa de Reservas </button>
                        </a>
                    )}
                    {!reserveData.action_required && <p>Tudo sob controle. Continue o bom trabalho!</p>}
                </div>
            );
        default:
            // Caso um módulo novo seja adicionado, a UI se adapta
            return <p>Conteúdo de Agente não implementado: **{moduleConfig.name}**</p>;
    }
  };

  return (
    // Estilo inline para posicionamento no CSS Grid
    <div className="panel" style={{ gridArea: moduleConfig.id }}> 
      <h2>{moduleConfig.name}</h2>
      <PanelContent />
    </div>
  );
};


// --- Componente Principal (Componente Pai) ---
function App() {
  const [dashboardConfig, setDashboardConfig] = useState<DashboardConfig | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Efeito principal para buscar e mesclar a configuração
  useEffect(() => {
    const fetchFullConfiguration = async () => {
      try {
        // 1. Obter Configuração de Sistema
        const systemResponse = await axios.get<SystemModuleDetail[]>(`${API_BASE_URL}/config/system/modules`);
        const systemModules = systemResponse.data;

        // 2. Obter Configuração do Usuário
        const userResponse = await axios.get<{ theme: string, modules: UserModulePreference[] }>(`${API_BASE_URL}/config/user/${USER_ID}`);
        const { theme, modules: userPreferences } = userResponse.data;

        // 3. Mesclar, Filtrar e Ordenar
        const activeModules: ActiveModuleConfig[] = userPreferences
          .filter(pref => pref.is_active) 
          .map(userPref => {
            const systemDetail = systemModules.find(sys => sys.id === userPref.module_id);
            if (!systemDetail) return null;
            
            return {
              ...systemDetail, 
              ...userPref,     
              // Adiciona o endpoint completo para o AgentPanel
              api_endpoint_full: `${API_BASE_URL}${systemDetail.api_endpoint}/${USER_ID}`,
            } as ActiveModuleConfig;
          })
          .filter((m): m is ActiveModuleConfig => m !== null) // Afirmação de tipo e remoção de nulos
          .sort((a, b) => a.display_order - b.display_order);

        setDashboardConfig({ theme, activeModules });

      } catch (err) {
        const fetchError = err as AxiosError;
        console.error("Erro ao carregar a configuração completa:", fetchError);
        setError(`Não foi possível carregar as configurações. Status: ${fetchError.response?.status || 'Offline'}.`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFullConfiguration();
  }, []); // [] garante que roda apenas na montagem

  // Efeito para aplicar a classe de tema no <body>
  useEffect(() => {
    if (dashboardConfig) {
      document.body.className = `theme-${dashboardConfig.theme || 'light'}`; 
    }
  }, [dashboardConfig?.theme]); 

  // --- Lógica de LAYOUT DINÂMICO (CSS Grid) - Otimizado com useMemo ---
  const dynamicGridStyle = useMemo<React.CSSProperties>(() => {
    if (!dashboardConfig) return {};

    const modules = dashboardConfig.activeModules;
    
    // Geração de colunas (Ex: "2fr 1fr 1fr")
    const columns = modules.map(m => `${m.grid_column_span}fr`).join(' ');
    // Geração de áreas (Ex: "context_agent" "skill_agent" "reserve_agent")
    const areas = modules.map(m => `"${m.id}"`).join(' '); 

    return {
        gridTemplateColumns: columns || '1fr', 
        gridTemplateAreas: areas,
        gridAutoRows: 'minmax(250px, auto)',
        gap: '20px' 
    };
  }, [dashboardConfig]);


  // --- Renderização ---
  if (isLoading) {
    return (
      <div className="status-container">
        <h1 className="main-title">FlowMaster AI</h1>
        <div className="status online">✅ Backend Online **(Carregando Configurações...)**</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="status-container">
        <h1 className="main-title">FlowMaster AI</h1>
        <div className="status offline">❌ Erro de Inicialização</div>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header>
        <h1 className="main-title">FlowMaster AI - Dashboard ({dashboardConfig?.theme})</h1>
        <p className={`status online`}>Status: **ONLINE**</p>
      </header>

      {/* Aplica o estilo dinâmico */}
      <div className="dashboard-grid" style={dynamicGridStyle}>
        {dashboardConfig.activeModules.map(module => (
          <AgentPanel key={module.id} moduleConfig={module} />
        ))}
      </div>
    </div>
  );
}

export default App;