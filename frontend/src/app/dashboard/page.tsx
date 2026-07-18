'use client';

import { useQuery } from '@tanstack/react-query';
import { KPICard } from '@/components/ui/KPICard';
import { PipelineChart } from '@/components/charts/PipelineChart';
import { QualityChart } from '@/components/charts/QualityChart';
import { RecentJobsTable } from '@/components/ui/RecentJobsTable';
import { analyticsApi } from '@/lib/api';
import { Database, CheckCircle, AlertTriangle, Zap } from 'lucide-react';

export default function DashboardPage() {
  const { data: kpis, isLoading } = useQuery({
    queryKey: ['kpis'],
    queryFn: () => analyticsApi.getKPIs(),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Real-time overview of your data pipelines</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Jobs Today"
          value={isLoading ? '...' : kpis?.jobs_today ?? 0}
          icon={<Zap className="h-4 w-4" />}
          trend="+12%"
          trendUp
        />
        <KPICard
          title="Active Sources"
          value={isLoading ? '...' : kpis?.total_sources ?? 0}
          icon={<Database className="h-4 w-4" />}
        />
        <KPICard
          title="Avg Quality Score"
          value="94.2%"
          icon={<CheckCircle className="h-4 w-4" />}
          trend="+2.1%"
          trendUp
        />
        <KPICard
          title="Platform Uptime"
          value={isLoading ? '...' : `${kpis?.platform_uptime_pct ?? 99.9}%`}
          icon={<AlertTriangle className="h-4 w-4" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PipelineChart />
        <QualityChart />
      </div>

      {/* Recent Jobs */}
      <RecentJobsTable />
    </div>
  );
}
