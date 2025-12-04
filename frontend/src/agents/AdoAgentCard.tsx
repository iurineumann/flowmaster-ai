// frontend/src/agents/AdoAgentCard.tsx

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { apiService } from '../services/apiClient'; // Usa o serviço centralizado
import type { AdoWorkItem } from '../types/models';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

interface AdoAgentCardProps {
  apiEndpoint?: string; // Opcional, pois usamos apiService
  title: string;
}

const AdoAgentCard: React.FC<AdoAgentCardProps> = ({ title }) => {
  const [items, setItems] = useState<AdoWorkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await apiService.getAdoWorkItems();
        // ✅ CORREÇÃO: Garante que é um array antes de setar
        setItems(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Erro ao buscar ADO:", err);
        setError("Não foi possível carregar as tarefas.");
        setItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getStatusIcon = (state: string) => {
    const s = state.toLowerCase();
    if (s.includes('done') || s.includes('closed') || s.includes('completed')) return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    if (s.includes('progress') || s.includes('active')) return <Clock className="w-4 h-4 text-blue-500" />;
    return <Circle className="w-4 h-4 text-gray-400" />;
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium flex items-center gap-2">
            <span className="bg-blue-100 text-blue-700 p-1 rounded">ADO</span>
            {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto">
        {loading ? (
           <div className="space-y-2">
             <div className="h-4 bg-muted rounded w-3/4 animate-pulse"></div>
             <div className="h-4 bg-muted rounded w-1/2 animate-pulse"></div>
           </div>
        ) : error ? (
            <p className="text-sm text-red-500">{error}</p>
        ) : items.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">Nenhuma tarefa atribuída.</p>
        ) : (
            <div className="space-y-3">
                {items.slice(0, 5).map(item => (
                    <div key={item.id} className="flex items-start gap-2 p-2 hover:bg-muted/50 rounded transition-colors group">
                        <div className="mt-1 shrink-0">{getStatusIcon(item.state)}</div>
                        <div className="min-w-0 flex-1">
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium hover:underline block truncate">
                                {item.title}
                            </a>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                                <span className="uppercase">{item.type}</span>
                                <span>•</span>
                                <span>{item.project}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AdoAgentCard;