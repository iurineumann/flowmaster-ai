import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { apiService } from '../services/apiClient';
import type { ReserveAgentResponse } from '../types/models';

const ReserveCard: React.FC<{ title?: string }> = ({ title = "Reserva" }) => {
    const [data, setData] = useState<ReserveAgentResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        apiService.getReserva()
            .then(res => { if (mounted) setData(res); })
            .catch(err => console.error("Erro ao buscar reserva:", err))
            .finally(() => { if (mounted) setLoading(false); });

        return () => { mounted = false; };
    }, []);

    if (loading) return <Skeleton className="h-[150px] w-full" />;

    return (
        <Card className="h-full bg-slate-50 dark:bg-slate-900">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent>
                {data ? (
                    <div>
                        <p className="text-sm">{data.resource_name} — {data.time_slot}</p>
                        <p className="text-xs text-muted-foreground mt-1">{data.reason}</p>
                    </div>
                ) : (
                    <p className="text-sm text-muted-foreground">Nenhuma sugestão de reserva.</p>
                )}
            </CardContent>
        </Card>
    );
};

export default ReserveCard;