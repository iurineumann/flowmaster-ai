// frontend/src/pages/AdminStatsPage.tsx

import React, { useEffect, useState } from 'react';
import { apiService } from '../services/apiClient';
import type { SystemStats } from '../types/models';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Componente de Card de Métrica Individual
const StatCard: React.FC<{ title: string; value: string | number; description: string }> = ({ title, value, description }) => (
    <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
            <div className="text-2xl font-bold">{value}</div>
            <p className="text-xs text-muted-foreground">{description}</p>
        </CardContent>
    </Card>
);

const AdminStatsPage: React.FC = () => {
    const [stats, setStats] = useState<SystemStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.getAdminStats()
            .then(data => setStats(data))
            .catch(err => console.error("Falha ao buscar estatísticas:", err))
            .finally(() => setLoading(false));
    }, []);

    // Prepara dados para os gráficos
    const cacheData = [
        { name: 'Hits', value: stats?.cache_hits || 0, fill: '#00A78E' }, // T2M Green
        { name: 'Misses', value: stats?.cache_misses || 0, fill: '#DC2626' } // Red
    ];

    const llmData = [
        { name: 'Chamadas LLM', value: stats?.total_llm_calls || 0, fill: '#2779A5' } // T2M Blue
    ];

    if (loading || !stats) {
        return (
            <main className="p-6 max-w-[1200px] mx-auto">
                <h1 className="text-3xl font-bold mb-6">Painel Administrativo</h1>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Skeleton className="h-[120px]" />
                    <Skeleton className="h-[120px]" />
                    <Skeleton className="h-[120px]" />
                    <Skeleton className="h-[120px]" />
                </div>
                <Skeleton className="h-[300px] mt-6" />
            </main>
        );
    }

    return (
        <main className="p-6 max-w-[1200px] mx-auto">
            <h1 className="text-3xl font-bold mb-6">Painel Administrativo</h1>
            
            {/* 1. Métricas Principais */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
                <StatCard 
                    title="Eficiência do Cache" 
                    value={stats.cache_efficiency} 
                    description="Total de Hits / Total de Requisições" 
                />
                <StatCard 
                    title="Custo (Chamadas LLM)" 
                    value={stats.total_llm_calls} 
                    description="Total de execuções de IA (não-cacheadas)" 
                />
                <StatCard 
                    title="Usuários Ativos (WS)" 
                    value={stats.active_ws_connections} 
                    description="Conexões WebSocket ativas no momento" 
                />
                <StatCard 
                    title="Usuários Registrados" 
                    value={stats.registered_users} 
                    description="Total de usuários na base de dados" 
                />
            </div>

            {/* 2. Gráficos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Performance do Cache (Hits vs. Misses)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={cacheData} layout="vertical">
                                <XAxis type="number" hide />
                                <YAxis type="category" dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} width={80} />
                                <Tooltip wrapperClassName="rounded-md shadow-lg" cursor={{ fill: 'rgba(240, 240, 240, 0.3)' }} />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {cacheData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardHeader>
                        <CardTitle>Custo de IA (Total de Chamadas LLM)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                         <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={llmData} layout="vertical">
                                <XAxis type="number" hide />
                                <YAxis type="category" dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} width={120} />
                                <Tooltip wrapperClassName="rounded-md shadow-lg" cursor={{ fill: 'rgba(240, 240, 240, 0.3)' }} />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]} fill={llmData[0].fill} />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </main>
    );
};

export default AdminStatsPage;