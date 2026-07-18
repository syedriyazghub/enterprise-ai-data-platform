'use client';

import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { analyticsApi } from '@/lib/api';

export function PipelineChart() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['pipeline-summary'],
    queryFn: () => analyticsApi.getSummary(),
    refetchInterval: 60_000,
  });

  const chartData = summary?.daily_breakdown ?? [
    { day: 'Mon', jobs: 0, records: 0 },
    { day: 'Tue', jobs: 0, records: 0 },
    { day: 'Wed', jobs: 0, records: 0 },
    { day: 'Thu', jobs: 0, records: 0 },
    { day: 'Fri', jobs: 0, records: 0 },
    { day: 'Sat', jobs: 0, records: 0 },
    { day: 'Sun', jobs: 0, records: 0 },
  ];

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">Pipeline Executions (Last 7 Days)</h3>
        {isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">Updating…</span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="jobsGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="recordsGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="day" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="left"  tick={{ fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
              fontSize: '12px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="jobs"
            name="Jobs"
            stroke="#3b82f6"
            fill="url(#jobsGrad)"
            strokeWidth={2}
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="records"
            name="Records"
            stroke="#10b981"
            fill="url(#recordsGrad)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
