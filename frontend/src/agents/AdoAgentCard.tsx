// frontend/src/agents/AdoAgentCard.tsx
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/apiClient';
import type { AdoWorkItem } from '../types/models';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { CheckSquare, Bug, ClipboardList } from 'lucide-react';

interface Props {
    apiEndpoint: string; // Recebido do App.tsx, embora usemos o apiService
    title: string;
}

const getItemIcon = (type: string) => {
    if (type.toLowerCase() === 'bug') {
        return <Bug className="w-4 h-4 text-destructive" />;
    }
    if (type.toLowerCase() === 'task') {
        return <CheckSquare className="w-4 h-4 text-blue-500" />;
    }
    return <ClipboardList className="w-4 h-4 text-gray-500" />;
};

const AdoAgentCard: React.FC<Props> = ({ apiEndpoint, title }) => {
    const [items, setItems] = useState<AdoWorkItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.getAdoWorkItems()
            .then(data => setItems(data))
            .catch(err => console.error("Erro ao buscar Work Items:", err))
            .finally(() => setLoading(false));
    }, [apiEndpoint]);

    if (loading) return <Skeleton className="h-[250px] w-full rounded-xl" />;

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="text-lg font-bold flex items-center gap-2">
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {items.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                        Nenhum Work Item ativo encontrado.
                    </p>
                ) : (
                    <ul className="space-y-3">
                        {items.slice(0, 5).map((item) => ( // Limita a 5
                            <li key={item.id} className="flex items-start gap-3">
                                <div>{getItemIcon(item.type)}</div>
                                <div className="flex-1">
                                    <a 
                                        href={item.url} 
                                        target="_blank" 
                                        rel="noreferrer" 
                                        className="text-sm font-medium hover:underline"
                                    >
                                        {item.title}
                                    </a>
                                    <div className="flex justify-between text-xs text-muted-foreground">
                                        <span>{item.organization}/{item.project}</span>
                                        <span>{item.state}</span>
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </CardContent>
        </Card>
    );
};

export default AdoAgentCard;