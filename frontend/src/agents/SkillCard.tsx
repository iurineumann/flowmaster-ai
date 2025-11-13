import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { SkillAgentData } from '../types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { Button } from '../components/ui/Button';
import { AlertTriangle, GraduationCap } from 'lucide-react';

interface SkillCardProps {
  apiEndpoint: string;
  title: string;
  description: string;
}

const SkillCard: React.FC<SkillCardProps> = ({ apiEndpoint, title, description }) => {
  const [data, setData] = useState<SkillAgentData | null>(null);
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
          <Skeleton className="h-6 w-1/2" />
          <Skeleton className="h-4 w-1/3" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
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
          <p className="text-sm text-destructive">Failed to load suggestions.</p>
          <Button variant="destructive" onClick={fetchData}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No skill suggestions available at the moment.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <GraduationCap className="mr-2 h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {data.suggestions.map((suggestion, index) => (
            <li key={index} className="flex items-center justify-between text-sm">
              {suggestion.link ? (
                <a href={suggestion.link} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                  {suggestion.title}
                </a>
              ) : (
                <span>{suggestion.title}</span>
              )}
              <span className="font-semibold">{Math.round(suggestion.relevance_score * 100)}%</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
};

export default SkillCard;
