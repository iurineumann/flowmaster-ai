// frontend/src/components/KnowledgePanel.tsx
import React from 'react';
import { SugestaoConhecimento } from '../interfaces';

interface KnowledgePanelProps {
    // Array de sugestões de conhecimento que vem do contexto agregado
    suggestions: SugestaoConhecimento[]; 
}

const KnowledgePanel: React.FC<KnowledgePanelProps> = ({ suggestions }) => (
    <div className="panel knowledge-panel">
        <h2>K-Search: Sugestões de Conhecimento</h2>
        {suggestions.length > 0 ? (
            suggestions.map((sugestao, index) => (
                <div key={index} className="suggestion-item">
                    <h4>{sugestao.title}</h4>
                    <p className="score">Relevância: {sugestao.score}</p>
                    <p>{sugestao.content_preview}</p>
                </div>
            ))
        ) : <p>A IA está indexando o conhecimento...</p>}
    </div>
);

export default KnowledgePanel;