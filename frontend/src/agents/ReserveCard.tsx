import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { MapPin } from 'lucide-react';

interface ReserveData {
    is_suggested: boolean;
    resource_name: string;
    reason: string;
}

const ReserveCard: React.FC<{ apiEndpoint: string, title: string }> = ({ apiEndpoint, title }) => {
    const [data, setData] = useState<ReserveData | null>(null);
    const [loading, setLoading] = useState(true);
    const token = localStorage.getItem('jwt_token');

    useEffect(() => {
        axios.get(apiEndpoint, { headers: { Authorization: `Bearer ${token}` } })
            .then(res => setData(res.data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, [apiEndpoint, token]);

    if (loading) return <Skeleton className="h-[150px] w-full" />;

    return (
        <Card className="h-full bg-slate-50 dark:bg-slate-900">
            <CardHeader className="pb-2">
                <CardTitle className="text-md font-medium flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-secondary" /> {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {data?.is_suggested ? (
                    <div className="bg-white dark:bg-slate-800 p-3 rounded border border-l-4 border-l-primary shadow-sm">
                        <p className="font-bold text-primary">{data.resource_name}</p>
                        <p className="text-xs text-muted-foreground mt-1">{data.reason}</p>
                        <button className="mt-2 w-full bg-primary text-white text-xs py-1 rounded hover:bg-primary/90">
                            Reservar Agora
                        </button>
                    </div>
                ) : (
                    <p className="text-sm text-muted-foreground">Nenhuma reserva necessária.</p>
                )}
            </CardContent>
        </Card>
    );
};

export default ReserveCard;