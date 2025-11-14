import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { AlertTriangle, CheckCircle, Brain } from 'lucide-react';

interface ContextData {
    foco_critico: string;
    resumo_ia: string;
    urgencia: number;
    sugestoes_conhecimento: any[];
}

interface Props {
    apiEndpoint: string;
    title: string;
}

const ContextCard: React.FC<Props> = ({ apiEndpoint, title }) => {
    const [data, setData] = useState<ContextData | null>(null);
    const [loading, setLoading] = useState(true);
    const token = localStorage.getItem('jwt_token');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get(apiEndpoint, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setData(response.data);
            } catch (error) {
                console.error("Erro ao buscar contexto:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [apiEndpoint, token]);

    if (loading) return <Skeleton className="h-[200px] w-full rounded-xl" />;
    if (!data) return <Card className="border-red-200"><CardContent className="p-6">Erro ao carregar contexto.</CardContent></Card>;

    const isCritical = data.urgencia >= 90;

    return (
        <Card className={`h-full ${isCritical ? 'border-red-500 border-l-4' : 'border-l-4 border-green-500'}`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                    {isCritical ? <AlertTriangle className="text-red-500" /> : <CheckCircle className="text-green-500" />}
                    {title}: {data.foco_critico}
                </CardTitle>
                <span className={`text-xs font-bold px-2 py-1 rounded ${isCritical ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                    Urgência: {data.urgencia}
                </span>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground mb-4">{data.resumo_ia}</p>
                
                {data.sugestoes_conhecimento?.length > 0 && (
                    <div className="mt-4 bg-muted/50 p-3 rounded-md">
                        <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                            <Brain className="w-4 h-4" /> IA Sugere (K-Search):
                        </h4>
                        <ul className="space-y-2">
                            {data.sugestoes_conhecimento.slice(0, 2).map((doc: any, idx: number) => (
                                <li key={idx} className="text-xs">
                                    <a href={doc.link} target="_blank" rel="noreferrer" className="text-primary hover:underline font-medium">
                                        {doc.title}
                                    </a>
                                    <p className="text-muted-foreground truncate">{doc.summary}</p>
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