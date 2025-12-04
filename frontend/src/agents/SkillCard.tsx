// frontend/src/agents/SkillCard.tsx

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { 
    BookOpen, 
    Info, 
    ExternalLink, 
    X, 
    PlayCircle, 
    FileText, 
    Award, 
    Tag 
} from 'lucide-react';
import { apiService } from '../services/apiClient';
import type { SkillAgentResponse, SkillItem } from '../types/models';

const SkillCard: React.FC<{ title: string }> = ({ title }) => {
    const [data, setData] = useState<SkillAgentResponse | null>(null);
    const [loading, setLoading] = useState(true);
    
    // Estado para controlar o Modal
    const [selectedSkill, setSelectedSkill] = useState<SkillItem | null>(null);

    useEffect(() => {
        apiService.getSkills()
            .then(res => setData(res))
            .catch(err => console.error("Erro ao buscar skills:", err))
            .finally(() => setLoading(false));
    }, []);

    // Helpers Visuais
    const getRelevancePercent = (relevance: string) => {
        const r = relevance.toLowerCase();
        return r.includes('alta') ? 90 : r.includes('média') || r.includes('media') ? 60 : 30;
    };

    const getRelevanceColor = (relevance: string) => {
        const r = relevance.toLowerCase();
        return r.includes('alta') ? 'bg-green-500' : (r.includes('média') || r.includes('media')) ? 'bg-yellow-500' : 'bg-blue-500';
    };

    const getTypeIcon = (type?: string) => {
        const t = (type || "").toLowerCase();
        if (t.includes('vídeo') || t.includes('video')) return <PlayCircle className="w-4 h-4 text-red-500" />;
        if (t.includes('curso')) return <Award className="w-4 h-4 text-purple-500" />;
        return <FileText className="w-4 h-4 text-blue-500" />;
    };

    if (loading) return <Skeleton className="h-[200px] w-full rounded-xl" />;

    return (
        <>
            {/* --- CARD PRINCIPAL --- */}
            <Card className="h-full flex flex-col">
                <CardHeader className="pb-2">
                    <CardTitle className="text-md font-medium flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-primary" /> {title}
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-auto custom-scrollbar">
                    <ul className="space-y-3">
                        {data && data.suggestions && data.suggestions.length > 0 ? (
                            data.suggestions.map((item, i) => (
                                <li 
                                    key={i} 
                                    onClick={() => setSelectedSkill(item)}
                                    className="group p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-all border border-transparent hover:border-border"
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <div className="flex items-center gap-2">
                                            {getTypeIcon(item.type)}
                                            <span className="text-sm font-medium leading-tight line-clamp-1">
                                                {item.skill}
                                            </span>
                                        </div>
                                        
                                        {/* Botão Link Direto (stopPropagation evita abrir o modal) */}
                                        {item.link && (
                                            <a 
                                                href={item.link} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                onClick={(e) => e.stopPropagation()} 
                                                className="text-muted-foreground hover:text-primary p-1 rounded-full hover:bg-background transition-colors"
                                                title="Abrir link externo agora"
                                            >
                                                <ExternalLink className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                    </div>
                                    
                                    {/* Barra de Relevância */}
                                    <div className="w-full bg-secondary rounded-full h-1.5 mb-1.5 mt-1">
                                        <div 
                                            className={`h-1.5 rounded-full transition-all duration-500 ${getRelevanceColor(item.relevancia)}`} 
                                            style={{ width: `${getRelevancePercent(item.relevancia)}%` }}
                                        ></div>
                                    </div>
                                    
                                    <p className="text-xs text-muted-foreground line-clamp-1">
                                        {item.motivo}
                                    </p>
                                </li>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-muted-foreground py-6">
                                <Info className="w-8 h-8 mb-2 opacity-20" />
                                <p className="text-sm">Sem recomendações no momento.</p>
                            </div>
                        )}
                    </ul>
                </CardContent>
            </Card>

            {/* --- MODAL DE DETALHES (Overlay) --- */}
            {selectedSkill && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div 
                        className="bg-background border border-border rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto flex flex-col animate-in zoom-in-95 duration-200"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header do Modal */}
                        <div className="flex items-center justify-between p-6 border-b border-border">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-primary/10 rounded-full">
                                    {getTypeIcon(selectedSkill.type)}
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                        {selectedSkill.type || "Recurso"} • {selectedSkill.source}
                                    </p>
                                    <h3 className="text-xl font-bold leading-tight mt-0.5">
                                        {selectedSkill.skill}
                                    </h3>
                                </div>
                            </div>
                            <button 
                                onClick={() => setSelectedSkill(null)}
                                className="text-muted-foreground hover:text-foreground p-2 hover:bg-muted rounded-full transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Conteúdo do Modal */}
                        <div className="p-6 space-y-6">
                            {/* Motivo (Por que isso é importante?) */}
                            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-100 dark:border-blue-900">
                                <h4 className="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-1 flex items-center gap-2">
                                    <Award className="w-4 h-4" /> Por que é recomendado?
                                </h4>
                                <p className="text-sm text-foreground/90">
                                    {selectedSkill.motivo}
                                </p>
                            </div>

                            {/* Resumo */}
                            <div>
                                <h4 className="text-sm font-semibold mb-2">Resumo do Conteúdo</h4>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    {selectedSkill.summary}
                                </p>
                            </div>

                            {/* Tags */}
                            {selectedSkill.tags && selectedSkill.tags.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                        <Tag className="w-3.5 h-3.5" /> Tópicos Relacionados
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedSkill.tags.map(tag => (
                                            <span key={tag} className="px-2.5 py-0.5 bg-secondary text-secondary-foreground rounded-md text-xs font-medium border border-border">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer / Ações */}
                        <div className="p-6 border-t border-border bg-muted/10 flex justify-end gap-3">
                            <Button variant="outline" onClick={() => setSelectedSkill(null)}>
                                Fechar
                            </Button>
                            {selectedSkill.link && (
                                <Button 
                                    onClick={() => window.open(selectedSkill.link, '_blank')}
                                    className="gap-2"
                                >
                                    Acessar Conteúdo <ExternalLink className="w-4 h-4" />
                                </Button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default SkillCard;