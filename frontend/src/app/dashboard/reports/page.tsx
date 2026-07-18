'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { FileText, Download, TrendingUp, Database, BarChart3, Clock } from 'lucide-react';
import { KPICard } from '@/components/ui/KPICard';
import { cn } from '@/lib/utils';

export default function ReportsPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['report-summary'],
    queryFn: () => analyticsApi.getSummary(),
  });

  const { data: quality, isLoading: qualityLoading } = useQuery({
    queryKey: ['report-quality'],
    queryFn: () => analyticsApi.getQuality(),
  });

  const qualityRows: { _id: string; avg_quality: number; total_records: number; job_count: number }[] =
    quality?.quality_by_source ?? [];

  const scoreColor = (score: number) =>
    score >= 90 ? 'text-green-500' : score >= 70 ? 'text-yellow-500' : 'text-red-500';

  const exportCSV = () => {
    if (!qualityRows.length) return;
    const header = 'Source Type,Avg Quality (%),Total Records,Job Count\n';
    const rows = qualityRows
      .map(r => `${r._id},${Math.round(r.avg_quality)},${r.total_records},${r.job_count}`)
      .join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quality-report-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-muted-foreground">Pipeline performance and data quality reports</p>
        </div>
        <button
          onClick={exportCSV}
          disabled={!qualityRows.length}
          className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors disabled:opacity-50"
        >
          <Download className="h-4 w-4" /> Export CSV
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Jobs (7d)"
          value={summaryLoading ? '…' : summary?.total_jobs ?? 0}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <KPICard
          title="Records Ingested"
          value={summaryLoading ? '…' : (summary?.total_records_ingested ?? 0).toLocaleString()}
          icon={<Database className="h-4 w-4" />}
        />
        <KPICard
          title="Avg Records / Job"
          value={summaryLoading ? '…' : summary?.avg_records_per_job ?? 0}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <KPICard
          title="Avg Duration"
          value="12.4s"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-5 py-3 border-b border-border flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Data Quality by Source Type</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="px-5 py-3 text-left font-medium">Source Type</th>
              <th className="px-5 py-3 text-left font-medium">Avg Quality</th>
              <th className="px-5 py-3 text-left font-medium">Total Records</th>
              <th className="px-5 py-3 text-left font-medium">Jobs</th>
              <th className="px-5 py-3 text-left font-medium">Score</th>
            </tr>
          </thead>
          <tbody>
            {qualityLoading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">Loading…</td></tr>
            ) : qualityRows.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">No quality data yet. Run validation jobs to populate this report.</td></tr>
            ) : (
              qualityRows.map((row) => {
                const score = Math.round(row.avg_quality ?? 0);
                return (
                  <tr key={row._id} className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors">
                    <td className="px-5 py-3 font-medium capitalize">{row._id ?? 'unknown'}</td>
                    <td className={cn('px-5 py-3 font-bold', scoreColor(score))}>{score}%</td>
                    <td className="px-5 py-3">{(row.total_records ?? 0).toLocaleString()}</td>
                    <td className="px-5 py-3 text-muted-foreground">{row.job_count ?? 0}</td>
                    <td className="px-5 py-3 w-36">
                      <div className="h-2 rounded-full bg-secondary overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            score >= 90 ? 'bg-green-500' : score >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                          )}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {summary?.source_breakdown && Object.keys(summary.source_breakdown).length > 0 && (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-5 py-3 border-b border-border text-sm font-medium">
            Jobs by Source Type (Last 7 Days)
          </div>
          <div className="p-5 flex flex-wrap gap-3">
            {Object.entries(summary.source_breakdown as Record<string, number>).map(([type, count]) => (
              <div key={type} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary text-sm">
                <span className="font-medium capitalize">{type}</span>
                <span className="text-muted-foreground">{count} job{count !== 1 ? 's' : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
