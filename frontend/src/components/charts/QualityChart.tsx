'use client';

import { useQuery } from '@tanstack/react-query';
import {
  RadialBarChart, RadialBar, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { analyticsApi } from '@/lib/api';

export function QualityChart() {
  const { data: quality, isLoading } = useQuery({
    queryKey: ['quality-metrics'],
    queryFn: () => analyticsApi.getQuality(),
    refetchInterval: 60_000,
  });

  const bySource: { name: string; score: number; fill: string }[] =
    (quality?.quality_by_source ?? []).map(
      (item: { _id: string; avg_quality: number }, i: number) => ({
        name: item._id ?? 'unknown',
        score: Math.round(item.avg_quality ?? 0),
        fill: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'][i % 6],
      })
    );

  const overallScore = bySource.length
    ? Math.round(bySource.reduce((s, x) => s + x.score, 0) / bySource.length)
    : 0;

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">Data Quality by Source</h3>
        {!isLoading && (
          <span className="text-xs font-medium text-green-500">
            Avg {overallScore}%
          </span>
        )}
        {isLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">Loading…</span>
        )}
      </div>

      {bySource.length === 0 ? (
        <div className="flex items-center justify-center h-[220px] text-muted-foreground text-sm">
          No quality data yet. Run a validation job to see scores.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={bySource} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
            <Tooltip
              formatter={(v: number) => [`${v}%`, 'Quality Score']}
              contentStyle={{
                background: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
                fontSize: '12px',
              }}
            />
            <Bar dataKey="score" name="Quality Score" radius={[0, 4, 4, 0]}>
              {bySource.map((entry, index) => (
                <rect key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
