// frontend/src/agents/ContextCard.tsx

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { Activity, Briefcase, Calendar, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/apiClient';
import type { ContextoAgregadoResponse } from '../types/models';

const ContextCard: React.FC<{ title: string }> = ({ title }) => {
    const [data, setData] = useState<ContextoAgregadoResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.getContexto()
            .then(res => setData(res))
            .catch(err => console.error("Erro Contexto:", err))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <Skeleton className="h-[200px] w-full" />;

    if (!data) return (
        <Card className="h-full">
            <CardContent className="p-6 text-center text-muted-foreground">
                Não foi possível carregar o contexto.
            </CardContent>
        </Card>
    );

    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="pb-2">
                <CardTitle className="text-md font-medium flex items-center gap-2">
                    <Activity className="w-4 h-4 text-primary" /> {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4">
                
                {/* Bloco Principal: Projeto Atual */}
                <div className="bg-primary/5 p-3 rounded-lg border border-primary/10">
                    <div className="flex items-center gap-2 mb-1">
                        <Briefcase className="w-4 h-4 text-primary" />
                        <span className="text-xs font-semibold text-primary uppercase">Foco Atual</span>
                    </div>
                    {/* ✅ CORREÇÃO: Uso de campos existentes */}
                    <p className="font-semibold text-lg leading-tight">{data.projeto_atual}</p>
                    <p className="text-sm text-muted-foreground">{data.funcao} • {data.sprint_atual}</p>
                </div>

                {/* Bloco Secundário: Métricas e Próxima Reunião */}
                <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 rounded-lg border bg-card">
                        <p className="text-xs text-muted-foreground">Tarefas Pendentes</p>
                        <p className="text-2xl font-bold">{data.tarefas_pendentes}</p>
                    </div>
                    <div className="p-3 rounded-lg border bg-card">
                        <div className="flex items-center gap-1 mb-1">
                            <Calendar className="w-3 h-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">Próxima Reunião</span>
                        </div>
                        <p className="text-sm font-medium truncate" title={data.proxima_reuniao || "Nenhuma"}>
                            {data.proxima_reuniao || "Livre"}
                        </p>
                    </div>
                </div>

                {/* Alertas (Substitui o antigo resumo_ia) */}
                {data.alertas && data.alertas.length > 0 && (
                    <div className="mt-auto">
                        <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                            <span className="text-xs font-medium text-amber-600 dark:text-amber-400">Atenção Necessária</span>
                        </div>
                        <ul className="text-sm space-y-1">
                            {data.alertas.map((alerta, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-muted-foreground">
                                    <span className="mt-1.5 w-1 h-1 rounded-full bg-amber-500 shrink-0" />
                                    {alerta}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default ContextCard;