import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { BookOpen } from 'lucide-react';

interface SkillData {
    suggestions: { title: string; relevance_score: number }[];
}

const SkillCard: React.FC<{ apiEndpoint: string, title: string }> = ({ apiEndpoint, title }) => {
    const [data, setData] = useState<SkillData | null>(null);
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
        <Card className="h-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-md font-medium flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-primary" /> {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ul className="space-y-3">
                    {data?.suggestions.map((skill, i) => (
                        <li key={i} className="flex justify-between items-center text-sm">
                            <span>{skill.title}</span>
                            <div className="w-16 bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                                <div className="bg-primary h-2.5 rounded-full" style={{ width: `${skill.relevance_score}%` }}></div>
                            </div>
                        </li>
                    ))}
                    {!data?.suggestions.length && <p className="text-sm text-muted-foreground">Nenhuma sugestão no momento.</p>}
                </ul>
            </CardContent>
        </Card>
    );
};

export default SkillCard;