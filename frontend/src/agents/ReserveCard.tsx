import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ReserveAgentData } from '../types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { Button } from '../components/ui/Button';
import { AlertTriangle, CalendarCheck } from 'lucide-react';

interface ReserveCardProps {
  apiEndpoint: string;
  title: string;
  description: string;
}

const ReserveCard: React.FC<ReserveCardProps> = ({ apiEndpoint, title, description }) => {
  const [data, setData] = useState<ReserveAgentData | null>(null);
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
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
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
          <p className="text-sm text-destructive">Failed to load suggestion.</p>
          <Button variant="destructive" onClick={fetchData}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.is_suggested) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No reservation suggested at this time.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <CalendarCheck className="mr-2 h-5 w-5 text-green-500" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">
          <strong>Resource:</strong> {data.resource_name}
        </p>
        <p className="text-sm">
          <strong>Time:</strong> {data.time_slot}
        </p>
        <p className="text-sm text-muted-foreground">{data.reason}</p>
        {data.link_to_map && (
          <Button asChild>
            <a href={data.link_to_map} target="_blank" rel="noopener noreferrer">
              View on Map
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default ReserveCard;
