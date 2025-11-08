// frontend/src/components/SkillReservePanel.tsx
import React from 'react';
import { SkillSuggestion, ReserveSuggestion } from '../interfaces';

interface SkillReserveProps {
    focoTitulo: string;
    skill: SkillSuggestion[];
    reserva: ReserveSuggestion | null;
}

// Componente para Skill-Boost
const SkillBoost: React.FC<{ skill: SkillSuggestion[], focoTitulo: string }> = ({ skill, focoTitulo }) => {
    const courseSuggestion = skill.find(s => s.type === 'course');
    const expertSuggestion = skill.find(s => s.type === 'expert');

    return (
        <div className="skill-boost-block">
            <h3>🧠 FlowMaster Skill-Boost</h3>
            <p>Baseado no seu foco ({focoTitulo}), a IA sugere:</p>
            
            {courseSuggestion && (
                <div className="suggestion-item">
                    <p>
                        **Curso Rápido:** {courseSuggestion.title}
                        <span className="score"> ({courseSuggestion.context_reason})</span>
                    </p>
                </div>
            )}
            
            {expertSuggestion && (
                <div className="suggestion-item">
                    <p>
                        **Especialista:** Fale com {expertSuggestion.title}
                        <span className="score"> ({expertSuggestion.context_reason})</span>
                    </p>
                </div>
            )}
             {skill.length === 0 && <p>A IA está calibrando o Skill-Boost para este projeto.</p>}
        </div>
    );
};

// Componente para Reserva Inteligente
const ReserveInteligente: React.FC<{ reserva: ReserveSuggestion | null }> = ({ reserva }) => (
    <div className="reserve-block">
        <h3>📍 Reserva de Posição Inteligente</h3>
        
        {reserva ? (
            <>
                <p className="suggestion-item">
                    Sugestão de Local: **{reserva.suggested_location}**
                </p>
                <p className="score">{reserva.reason}</p>
                <button>Reservar {reserva.resource_id}</button>
            </>
        ) : <p>A IA está analisando o mapa de reservas...</p>}
    </div>
);


const SkillReservePanel: React.FC<SkillReserveProps> = ({ focoTitulo, skill, reserva }) => {
    return (
        <div className="panel skill-reserve-panel">
            <h2>Skill-Boost e Reserva Inteligente</h2>
            <SkillBoost skill={skill} focoTitulo={focoTitulo} />
            <ReserveInteligente reserva={reserva} />
        </div>
    );
};

export default SkillReservePanel;