import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ContextAgentData } from '../types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { Button } from '../components/ui/Button';
import { AlertTriangle, Lightbulb } from 'lucide-react';

interface ContextCardProps {
  apiEndpoint: string;
  title: string;
  description: string;
}

const ContextCard: React.FC<ContextCardProps> = ({ apiEndpoint, title, description }) => {
  const [data, setData] = useState<ContextAgentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(apiEndpoint);
      setData(response.data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [apiEndpoint]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-8 w-1/3" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center text-destructive">
            <AlertTriangle className="mr-2 h-5 w-5" />
            {title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center space-y-4">
          <p className="text-sm text-destructive">Failed to load data.</p>
          <Button variant="destructive" onClick={fetchData}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{data.resumo_llm.focus_title}</CardTitle>
        <CardDescription>
          <strong>{data.foco_critico}:</strong> {data.foco_detalhe}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <h4 className="font-semibold">AI Summary & Analysis</h4>
          <p className="text-sm text-muted-foreground">{data.resumo_llm.summary_analysis}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {data.resumo_llm.technical_tags.map(tag => (
              <span key={tag} className="rounded-full bg-secondary px-2 py-1 text-xs text-secondary-foreground">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h4 className="mb-2 flex items-center font-semibold">
            <Lightbulb className="mr-2 h-5 w-5 text-yellow-400" />
            Knowledge Suggestions
          </h4>
          <ul className="space-y-2">
            {data.sugestoes_conhecimento.map(sugestion => (
              <li key={sugestion.link} className="text-sm">
                <a href={sugestion.link} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                  {sugestion.title}
                </a>
                <p className="text-xs text-muted-foreground">{sugestion.summary}</p>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default ContextCard;
