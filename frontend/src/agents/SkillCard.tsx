// frontend/src/agents/SkillCard.tsx

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { BookOpen } from 'lucide-react';
import { apiService } from '../services/apiClient';
// ✅ CORREÇÃO: Importa a interface correta
import type { SkillAgentResponse } from '../types/models';

const SkillCard: React.FC<{ apiEndpoint: string, title: string }> = ({ title }) => {
    // ✅ CORREÇÃO: Usa a interface correta no useState
    const [data, setData] = useState<SkillAgentResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // ✅ CORREÇÃO: Usa o apiService
        apiService.getSkills()
            .then(res => setData(res))
            .catch(err => console.error("Erro ao buscar skills:", err))
            .finally(() => setLoading(false));
    }, []); // Remove a dependência de apiEndpoint (não é mais necessária)

    if (loading) return <Skeleton className="h-[150px] w-full" />;

    return (
        <Card className="h-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-md font-medium flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-primary" /> {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ul className="space-y-3">
                    {/* ✅ CORREÇÃO: data.suggestions agora existe */}
                    {data && data.suggestions.length > 0 ? (
                        data.suggestions.map((skill, i) => (
                            <li key={i} className="flex justify-between items-center text-sm">
                                <span>{skill.title}</span>
                                <div className="w-16 bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                                    <div className="bg-primary h-2.5 rounded-full" style={{ width: `${skill.relevance_score}%` }}></div>
                                </div>
                            </li>
                        ))
                    ) : (
                        <p className="text-sm text-muted-foreground">Nenhuma sugestão no momento.</p>
                    )}
                </ul>
            </CardContent>
        </Card>
    );
};

export default SkillCard;