import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: string;
  trendUp?: boolean;
  className?: string;
}

export function KPICard({ title, value, icon, trend, trendUp, className }: KPICardProps) {
  return (
    <div className={cn('rounded-lg border border-border bg-card p-5 shadow-sm', className)}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <span className="text-muted-foreground">{icon}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      {trend && (
        <p className={cn('text-xs mt-1', trendUp ? 'text-green-500' : 'text-red-500')}>
          {trendUp ? '↑' : '↓'} {trend} from last period
        </p>
      )}
    </div>
  );
}
