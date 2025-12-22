// frontend/src/agents/SkillCard.tsx

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
// Ícones Lucide (Padrão moderno)
import { 
    BookOpen, 
    Info, 
    ExternalLink, 
    X, 
    PlayCircle, 
    FileText, 
    Award, 
    Tag, 
    ArrowRight 
} from 'lucide-react';
import { apiService } from '../services/apiClient';
import type { SkillAgentResponse, SkillItem } from '../types/models';

const SkillCard: React.FC<{ title: string }> = ({ title }) => {
    const [data, setData] = useState<SkillAgentResponse | null>(null);
    const [loading, setLoading] = useState(true);
    
    // Estado para controlar qual skill está aberta no modal
    const [selectedSkill, setSelectedSkill] = useState<SkillItem | null>(null);

    useEffect(() => {
        apiService.getSkills()
            .then(res => setData(res))
            .catch(err => console.error("Erro ao buscar skills:", err))
            .finally(() => setLoading(false));
    }, []);

    // Helpers de UI
    const getRelevanceColor = (relevance: string) => {
        const r = relevance.toLowerCase();
        if (r.includes('alta')) return 'bg-green-500';
        if (r.includes('média') || r.includes('media')) return 'bg-yellow-500';
        return 'bg-blue-500';
    };

    const getTypeIcon = (type?: string) => {
        const t = (type || "").toLowerCase();
        if (t.includes('vídeo') || t.includes('video')) return <PlayCircle className="w-5 h-5 text-red-500" />;
        if (t.includes('curso')) return <Award className="w-5 h-5 text-purple-500" />;
        return <FileText className="w-5 h-5 text-blue-500" />;
    };

    if (loading) return <Skeleton className="h-[250px] w-full rounded-xl" />;

    return (
        <>
            {/* --- CARD PRINCIPAL (Lista) --- */}
            <Card className="h-full flex flex-col shadow-sm border-t-4 border-t-primary">
                <CardHeader className="pb-3 border-b border-border/40">
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-primary" /> {title}
                    </CardTitle>
                </CardHeader>
                
                <CardContent className="flex-1 overflow-auto p-0">
                    <ul className="divide-y divide-border/40">
                        {data && data.suggestions && data.suggestions.length > 0 ? (
                            data.suggestions.map((item, i) => (
                                <li 
                                    key={i} 
                                    onClick={() => setSelectedSkill(item)}
                                    className="group p-4 hover:bg-muted/40 cursor-pointer transition-colors flex items-start gap-3"
                                >
                                    {/* Ícone do Tipo */}
                                    <div className="mt-1 shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                                        {getTypeIcon(item.type)}
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="text-sm font-semibold text-foreground/90 group-hover:text-primary transition-colors line-clamp-1">
                                                {item.skill}
                                            </span>
                                            {/* Badge de Relevância */}
                                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded text-white ${getRelevanceColor(item.relevancia)}`}>
                                                {item.relevancia.toUpperCase()}
                                            </span>
                                        </div>
                                        
                                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                                            {item.motivo}
                                        </p>
                                        
                                        {/* Botão Ação Rápida (Sutil) */}
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                             <span className="text-xs text-primary font-medium flex items-center">
                                                Ver detalhes <ArrowRight className="w-3 h-3 ml-1" />
                                             </span>
                                             {item.link && (
                                                 <a 
                                                    href={item.link} 
                                                    target="_blank" 
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="p-1 hover:bg-background rounded-full border border-transparent hover:border-border"
                                                    title="Abrir link externo"
                                                 >
                                                     <ExternalLink className="w-3 h-3 text-muted-foreground hover:text-foreground" />
                                                 </a>
                                             )}
                                        </div>
                                    </div>
                                </li>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                                <Info className="w-8 h-8 mb-2 opacity-20" />
                                <p className="text-sm">Sem recomendações no momento.</p>
                            </div>
                        )}
                    </ul>
                </CardContent>
            </Card>

            {/* --- MODAL DE DETALHES (Dialog) --- */}
            {selectedSkill && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
                    <div 
                        className="bg-background border border-border rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto flex flex-col animate-in zoom-in-95 duration-200"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header Modal */}
                        <div className="flex items-start justify-between p-6 border-b border-border bg-muted/10">
                            <div className="flex gap-4">
                                <div className="p-3 bg-background rounded-xl shadow-sm border border-border">
                                    {getTypeIcon(selectedSkill.type)}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                            {selectedSkill.type || "Recurso"}
                                        </span>
                                        <span className="text-xs text-muted-foreground">•</span>
                                        <span className="text-xs text-muted-foreground font-medium">
                                            Fonte: {selectedSkill.source || "Web"}
                                        </span>
                                    </div>
                                    <h3 className="text-xl font-bold leading-tight text-foreground">
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

                        {/* Body Modal */}
                        <div className="p-6 space-y-6">
                            {/* Seção: Por que isso é importante? */}
                            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-100 dark:border-blue-900/50">
                                <h4 className="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-1 flex items-center gap-2">
                                    <Award className="w-4 h-4" /> Por que a IA recomendou isso?
                                </h4>
                                <p className="text-sm text-foreground/90 leading-relaxed">
                                    {selectedSkill.motivo}
                                </p>
                            </div>

                            {/* Seção: Resumo */}
                            <div>
                                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-muted-foreground" /> Resumo do Conteúdo
                                </h4>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    {selectedSkill.summary}
                                </p>
                            </div>

                            {/* Seção: Tags */}
                            {selectedSkill.tags && selectedSkill.tags.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                                        <Tag className="w-4 h-4 text-muted-foreground" /> Tópicos Relacionados
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedSkill.tags.map(tag => (
                                            <span key={tag} className="px-2.5 py-1 bg-secondary text-secondary-foreground rounded-md text-xs font-medium border border-border/50">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer Modal */}
                        <div className="p-6 border-t border-border bg-muted/5 flex justify-end gap-3">
                            <Button variant="outline" onClick={() => setSelectedSkill(null)}>
                                Fechar
                            </Button>
                            {selectedSkill.link && (
                                <Button 
                                    onClick={() => window.open(selectedSkill.link, '_blank')}
                                    className="gap-2 shadow-md hover:scale-[1.02] transition-transform"
                                >
                                    Acessar Agora <ExternalLink className="w-4 h-4" />
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