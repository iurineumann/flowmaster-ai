// frontend/src/App.tsx (Orquestrador Principal em TypeScript)
import { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';

// Importa Interfaces e Componentes Modularizados
import { ContextoAgregado, SkillSuggestion, ReserveSuggestion } from './interfaces';
import HeaderStatus from './components/HeaderStatus';
import ContextPanel from './components/ContextPanel';
import KnowledgePanel from './components/KnowledgePanel';
import SkillReservePanel from './components/SkillReservePanel';

const DEFAULT_PROJECT_TAG = 'CLIENTE_X'; 

function App() {
  const [backendStatus, setBackendStatus] = useState('Offline');
  // Usa os Tipos (Interfaces) para garantir a qualidade do código
  const [contexto, setContexto] = useState<ContextoAgregado | null>(null);
  const [skill, setSkill] = useState<SkillSuggestion[]>([]);
  const [reserva, setReserva] = useState<ReserveSuggestion | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setBackendStatus('Conectando...');
        
        // Dispara todas as requisições em paralelo (Performance)
        const contextPromise = axios.get<ContextoAgregado>('/api/contexto/agregado/42');
        const skillPromise = axios.get<SkillSuggestion[]>(`/api/skill/suggestions/${DEFAULT_PROJECT_TAG}`);
        const reservePromise = axios.get<ReserveSuggestion>(`/api/reserva/suggestion/${DEFAULT_PROJECT_TAG}`);

        const [contextResponse, skillResponse, reserveResponse] = await Promise.all([
            contextPromise, 
            skillPromise, 
            reservePromise
        ]);

        // Armazena os dados
        setContexto(contextResponse.data);
        setSkill(skillResponse.data);
        setReserva(reserveResponse.data);
        
        setBackendStatus(`Online (Foco: ${DEFAULT_PROJECT_TAG})`);
        
      } catch (error) {
        console.error("Erro ao buscar dados da IA:", error);
        setBackendStatus('Offline ou Erro de API');
      }
    };

    fetchData();
    // Re-analisa o contexto a cada 30 segundos
    const interval = setInterval(fetchData, 30000); 
    return () => clearInterval(interval);
  }, []);

  // Determina o foco para passar aos subcomponentes
  const focoAtualTitulo = contexto?.foco_atual_titulo || 'Carregando Foco...';

  return (
    <div className="App">
      <HeaderStatus status={backendStatus} />

      <div className="dashboard-grid">
        {/* Coluna 1 (2fr): Foco Crítico */}
        <ContextPanel contexto={contexto} /> 
        
        {/* Coluna 2 (2fr): K-Search / Conhecimento */}
        <KnowledgePanel suggestions={contexto?.sugestoes_conhecimento || []} />
        
        {/* Coluna 3 (1.5fr): Skill-Boost e Reserva */}
        <SkillReservePanel 
            focoTitulo={focoAtualTitulo}
            skill={skill}
            reserva={reserva}
        />
      </div>
    </div>
  );
}

export default App;