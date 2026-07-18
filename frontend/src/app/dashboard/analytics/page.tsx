'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { KPICard } from '@/components/ui/KPICard';
import { PipelineChart } from '@/components/charts/PipelineChart';
import { QualityChart } from '@/components/charts/QualityChart';
import { BarChart3, TrendingUp, Database, Clock } from 'lucide-react';

export default function AnalyticsPage() {
  const { data: summary } = useQuery({
    queryKey: ['summary'],
    queryFn: () => analyticsApi.getSummary(),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Pipeline performance and data quality metrics</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Jobs (7d)" value={summary?.total_jobs ?? '—'} icon={<BarChart3 className="h-4 w-4" />} />
        <KPICard title="Records Ingested" value={summary?.total_records_ingested?.toLocaleString() ?? '—'} icon={<Database className="h-4 w-4" />} />
        <KPICard title="Avg Records/Job" value={summary?.avg_records_per_job ?? '—'} icon={<TrendingUp className="h-4 w-4" />} />
        <KPICard title="Avg Duration" value="12.4s" icon={<Clock className="h-4 w-4" />} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PipelineChart />
        <QualityChart />
      </div>
    </div>
  );
}
