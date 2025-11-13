// frontend/src/App.tsx - INTEGRAÇÃO FINAL DE LOGIN

import React, { useEffect, useState, useCallback } from 'react';
import Login from './Login'; // NOVO: Importa o componente de login
import { fetchUserConfig, fetchContextoAgregado } from './services/apiClient';
import { initWebSocket, closeWebSocket } from './services/websocketService';
import type { UserConfig, ContextoAgregadoResponse, CriticalBugAlert } from './types/models';

const App: React.FC = () => {
    // Estado para autenticação
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('jwt_token'));
    
    // Estados do Dashboard
    const [config, setConfig] = useState<UserConfig | null>(null);
    const [contexto, setContexto] = useState<ContextoAgregadoResponse | null>(null);
    const [criticalAlert, setCriticalAlert] = useState<CriticalBugAlert | null>(null);
    const [loading, setLoading] = useState<boolean>(false); // Inicializa como false, pois a lógica de load está no useEffect
    const [error, setError] = useState<string | null>(null);

    // Função para tratar o sucesso do Login
    const handleLoginSuccess = useCallback((token: string) => {
        // O token já está no localStorage. Apenas atualiza o estado
        setIsAuthenticated(true);
        console.log(`Login bem-sucedido, token armazenado: ${token}`);
        // O useEffect será disparado para carregar os dados
    }, []);

    // --- Lógica de Inicialização do Dashboard ---
    useEffect(() => {
        const token = localStorage.getItem('jwt_token');

        // Se não houver token, para a execução do useEffect
        if (!token) {
            setIsAuthenticated(false);
            return;
        }

        const loadDashboardData = async () => {
            setLoading(true);
            setError(null);
            
            try {
                // 1. Carga Inicial: Configuração (Estrutura do Dashboard)
                const userConfig = await fetchUserConfig();
                setConfig(userConfig);

                // 2. Carga Principal: Contexto (Conteúdo dos Widgets)
                const contextoData = await fetchContextoAgregado();
                setContexto(contextoData);

            } catch (err: any) {
                console.error("Erro ao carregar dados do dashboard:", err);
                // Se a API retornar 401 (token expirado), força o logout
                if (err.response && err.response.status === 401) {
                    localStorage.removeItem('jwt_token');
                    setIsAuthenticated(false);
                    setError("Sessão expirada. Por favor, faça login novamente.");
                } else {
                    setError(`Falha na API: ${err.message}. Verifique se o backend está rodando em :8000.`);
                }
            } finally {
                setLoading(false);
            }
        };

        const initRealTime = () => {
            // 3. Inicia a Conexão WebSocket (Squad 2)
            const handleCriticalAlert = (alert: CriticalBugAlert) => {
                setCriticalAlert(alert);
                console.log("ALERTA CRÍTICO RECEBIDO:", alert);
            };

            initWebSocket(token, handleCriticalAlert);
        }
        
        loadDashboardData();
        initRealTime();


        // 4. Limpeza: Fecha a conexão WS ao desmontar o componente
        return () => {
            closeWebSocket();
        };

    }, [isAuthenticated]); // Executa na montagem OU quando o estado de autenticação muda

    // Renderiza a tela de Login se não estiver autenticado
    if (!isAuthenticated) {
        // Se houver um erro de sessão expirada, exibe a mensagem no Login
        return <Login onLoginSuccess={handleLoginSuccess} />; 
    }
    
    // Renderização do Dashboard
    if (loading) return <div>Carregando Dashboard...</div>;
    if (error) return <div style={{ color: 'red', padding: '20px' }}>Erro: {error}</div>;
    if (!config || !contexto) return <div>Dados Incompletos ou Carregando...</div>;


    // --- Renderização da UI (Dashboard) ---
    return (
        <div style={{ padding: '20px', fontFamily: 'Arial' }}>
            <h1>FlowMaster AI - Dashboard (Usuário: {config.user_id})</h1>
            
            {/* ... (O restante da UI do Dashboard permanece inalterado) ... */}
            
            {/* Widget de Alerta Crítico (Squad 2) */}
            {criticalAlert && (
                <div style={{ border: '2px solid red', padding: '15px', marginBottom: '20px', backgroundColor: '#fee' }}>
                    <h2>🚨 ALERTA CRÍTICO (URGÊNCIA: {criticalAlert.urgency})</h2>
                    <h3>{criticalAlert.title}</h3>
                    <p>{criticalAlert.detail}</p>
                    <button onClick={() => setCriticalAlert(null)}>Resolver</button>
                </div>
            )}

            {/* Configuração do Usuário (Squad 1) */}
            <p><strong>Tema Ativo:</strong> {config.theme}</p>
            <p><strong>Módulos Ativos (Ordem):</strong> {config.modules
                .filter(m => m.is_active)
                .sort((a, b) => a.display_order - b.display_order)
                .map(m => m.module_id)
                .join(', ')}</p>

            {/* Foco Crítico (Squad 1) */}
            <div style={{ border: '1px solid #ccc', padding: '15px', marginTop: '20px' }}>
                <h2>Foco Crítico do Agente (Score: {contexto.foco_critico.urgency_score})</h2>
                <h3>{contexto.foco_critico.title}</h3>
                <p><strong>Análise:</strong> {contexto.foco_critico.summary_analysis}</p>
            </div>

            {/* Sugestões de Conhecimento (K-Search) */}
            <div style={{ marginTop: '20px' }}>
                <h2>Sugestões de Conhecimento Relevante</h2>
                <ul>
                    {contexto.sugestoes_conhecimento.map((s, index) => (
                        <li key={index}>
                            <strong>{s.title} ({s.score}%)</strong> - <a href={s.link} target="_blank">Abrir</a>
                            <p style={{ margin: '5px 0 0 0', fontSize: '0.9em' }}>{s.summary}</p>
                        </li>
                    ))}
                </ul>
            </div>
            {/* Botão de Logout para testes */}
            <button 
                onClick={() => {
                    localStorage.removeItem('jwt_token');
                    setIsAuthenticated(false);
                    // Força o reload da página para limpar o estado se necessário
                    window.location.reload(); 
                }}
                style={{ position: 'fixed', top: '10px', right: '10px', padding: '8px 15px' }}
            >
                Sair
            </button>
        </div>
    );
};

export default App;