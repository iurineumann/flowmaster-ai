// frontend/src/components/ContextPanel.tsx (FOCA APENAS NO FOCO CRÍTICO)
import React from 'react';
import { ContextoAgregado } from '../interfaces';

interface ContextPanelProps {
    contexto: ContextoAgregado | null;
}

const ContextPanel: React.FC<ContextPanelProps> = ({ contexto }) => {
    if (!contexto) {
        return <div className="panel context-panel"><h2>Carregando Contexto...</h2></div>;
    }

    return (
        <div className="panel context-panel">
            <h2>Seu Foco Atual (Agregado pela IA)</h2>
            <h3>{contexto.foco_atual_titulo}</h3>
            <p className="resumo">**Resumo IA:** {contexto.resumo_ia}</p>
            <p>Próxima Reunião: **{contexto.proxima_reuniao}**</p>
            <button>Ver Detalhes do Projeto</button>
        </div>
    );
};

export default ContextPanel;