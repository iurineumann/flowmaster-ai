// frontend/src/agents/MeetingCard.tsx

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { 
    Users, 
    AlertOctagon, 
    Check, 
    Clock, 
    ArrowRight,
    CalendarCheck
} from 'lucide-react';
import { apiService } from '../services/apiClient';
import type { MeetingAgentResponse } from '../types/models';

const MeetingCard: React.FC<{ title: string }> = ({ title }) => {
    const [data, setData] = useState<MeetingAgentResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.getMeeting()
            .then(res => setData(res))
            .catch(err => console.error("Erro ao buscar reuniões:", err))
            .finally(() => setLoading(false));
    }, []);

    // Loading State
    if (loading) return <Skeleton className="h-[250px] w-full rounded-xl" />;

    // Empty State
    if (!data || !data.is_required) {
        return (
            <Card className="h-full flex flex-col justify-center items-center p-6 text-center text-muted-foreground opacity-70 border-dashed">
                <Users className="w-8 h-8 mb-2 opacity-20" />
                <p className="text-sm font-medium">Nenhuma reunião crítica pendente.</p>
                <p className="text-xs mt-1">Sua agenda está otimizada.</p>
            </Card>
        );
    }

    const isHighPriority = data.priority === 'Alta';

    return (
        <Card className={`h-full flex flex-col shadow-sm transition-all duration-300 hover:shadow-md ${
            isHighPriority ? 'border-l-4 border-l-red-500 bg-red-50/10 dark:bg-red-900/10' : 'border-l-4 border-l-orange-500'
        }`}>
            <CardHeader className="pb-2">
                <CardTitle className="text-md font-medium flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Users className={`w-4 h-4 ${isHighPriority ? 'text-red-600' : 'text-orange-500'}`} /> 
                        {title}
                    </div>
                    {isHighPriority && (
                        <span className="animate-pulse text-[10px] bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-100 px-2 py-0.5 rounded-full uppercase tracking-wide font-bold border border-red-200">
                            Urgente
                        </span>
                    )}
                </CardTitle>
            </CardHeader>
            
            <CardContent className="flex-1 flex flex-col">
                {/* Título e Motivo */}
                <div className="mb-4">
                    <h3 className="text-lg font-bold leading-tight mb-1.5 text-foreground">
                        {data.title}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <AlertOctagon className="w-3.5 h-3.5" />
                        <span className="font-medium">Motivo:</span> {data.context_source}
                    </div>
                </div>

                {/* Pauta Sugerida (Box) */}
                <div className="bg-background/50 border border-border p-3 rounded-lg mb-4 flex-1">
                    <div className="flex justify-between items-center mb-2">
                        <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
                            Pauta Sugerida
                        </p>
                        <div className="flex items-center gap-1 text-xs font-medium text-primary">
                            <Clock className="w-3 h-3" /> {data.duration_minutes} min
                        </div>
                    </div>
                    
                    <ul className="space-y-1.5">
                        {data.suggested_agenda.map((item, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                                <Check className="w-3.5 h-3.5 mt-0.5 text-green-600 shrink-0" />
                                <span className="leading-tight text-foreground/90">{item}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Ações */}
                <div className="mt-auto pt-2">
                    <Button 
                        variant={isHighPriority ? "destructive" : "default"} 
                        className="w-full gap-2 shadow-sm hover:shadow group"
                        onClick={() => window.open('https://outlook.office.com/calendar/', '_blank')}
                    >
                        <CalendarCheck className="w-4 h-4" /> 
                        Agendar Reunião
                        <ArrowRight className="w-3 h-3 opacity-70 group-hover:translate-x-0.5 transition-transform" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

export default MeetingCard;