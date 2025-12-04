export type NotificationType = 'CRITICAL_BUG_ALERT' | 'INFO' | 'WARNING';

export interface CriticalBugAlert {
  type: 'CRITICAL_BUG_ALERT';
  title: string;
  urgency: number;
  detail: string;
}

export type AppNotification = CriticalBugAlert;