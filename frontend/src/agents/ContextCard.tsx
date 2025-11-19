import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { apiService } from '../services/apiClient'; // <-- usa apiService
import type { ContextoAgregadoResponse } from '../types/models';

const ContextCard: React.FC<{ title?: string }> = ({ title = "Contexto" }) => {
    const [data, setData] = useState<ContextoAgregadoResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;
        apiService.getContexto()
            .then(res => { if (mounted) setData(res); })
            .catch(err => console.error("Erro ao buscar contexto:", err))
            .finally(() => { if (mounted) setLoading(false); });

        return () => { mounted = false; };
    }, []);

    if (loading) return <Skeleton className="h-[150px] w-full" />;

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent>
                {data ? (
                    <>
                        <p className="font-semibold">{data.foco_critico}</p>
                        <p className="text-sm text-muted-foreground mt-2">{data.resumo_ia}</p>
                    </>
                ) : (
                    <p className="text-sm text-muted-foreground">Nenhum contexto disponível.</p>
                )}
            </CardContent>
        </Card>
    );
};

export default ContextCard;