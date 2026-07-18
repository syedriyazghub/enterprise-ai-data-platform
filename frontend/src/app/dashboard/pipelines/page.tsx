'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ingestionApi } from '@/lib/api';
import { Play, RefreshCw, Clock, CheckCircle, XCircle, Loader2, GitBranch } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
  completed: { label: 'Completed', icon: <CheckCircle className="h-3 w-3" />, cls: 'text-green-500 bg-green-500/10' },
  running:   { label: 'Running',   icon: <Loader2 className="h-3 w-3 animate-spin" />, cls: 'text-blue-500 bg-blue-500/10' },
  failed:    { label: 'Failed',    icon: <XCircle className="h-3 w-3" />, cls: 'text-red-500 bg-red-500/10' },
  pending:   { label: 'Pending',   icon: <Clock className="h-3 w-3" />, cls: 'text-yellow-500 bg-yellow-500/10' },
};

export default function PipelinesPage() {
  const qc = useQueryClient();

  const { data: sources } = useQuery({
    queryKey: ['sources'],
    queryFn: () => ingestionApi.getSources(),
  });

  const { data: jobs, isLoading, refetch } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => ingestionApi.getJobs(),
    refetchInterval: 10_000,
  });

  const triggerMutation = useMutation({
    mutationFn: (sourceId: string) => ingestionApi.triggerJob(sourceId),
    onSuccess: () => {
      toast.success('Pipeline triggered');
      qc.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: () => toast.error('Failed to trigger pipeline'),
  });

  const jobList: Record<string, unknown>[] = jobs?.items ?? [];
  const sourceList: Record<string, unknown>[] = sources?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Pipelines</h1>
          <p className="text-muted-foreground">Trigger and monitor ingestion pipeline executions</p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-md border border-border hover:bg-accent transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Trigger Panel */}
      {sourceList.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-5">
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <GitBranch className="h-4 w-4" /> Trigger Pipeline
          </h2>
          <div className="flex flex-wrap gap-2">
            {sourceList.map((s) => (
              <button
                key={s.id as string}
                onClick={() => triggerMutation.mutate(s.id as string)}
                disabled={triggerMutation.isPending}
                className="flex items-center gap-2 px-3 py-1.5 text-xs rounded-md border border-border hover:bg-accent transition-colors disabled:opacity-50"
              >
                <Play className="h-3 w-3" />
                {s.name as string}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Jobs Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-5 py-3 border-b border-border">
          <span className="text-sm font-medium">Execution History</span>
          <span className="ml-2 text-xs text-muted-foreground">({jobs?.total ?? 0} total)</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="px-5 py-3 text-left font-medium">Job ID</th>
              <th className="px-5 py-3 text-left font-medium">Status</th>
              <th className="px-5 py-3 text-left font-medium">Records</th>
              <th className="px-5 py-3 text-left font-medium">Started</th>
              <th className="px-5 py-3 text-left font-medium">Duration</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">Loading…</td></tr>
            ) : jobList.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">No pipeline executions yet.</td></tr>
            ) : (
              jobList.map((j) => {
                const cfg = STATUS_CONFIG[j.status as string] ?? STATUS_CONFIG.pending;
                const started = j.started_at ? new Date(j.started_at as string) : null;
                const completed = j.completed_at ? new Date(j.completed_at as string) : null;
                const durationSec = started && completed
                  ? ((completed.getTime() - started.getTime()) / 1000).toFixed(1)
                  : '—';
                return (
                  <tr key={j.id as string} className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors">
                    <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                      {(j.id as string).slice(0, 8)}…
                    </td>
                    <td className="px-5 py-3">
                      <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', cfg.cls)}>
                        {cfg.icon} {cfg.label}
                      </span>
                    </td>
                    <td className="px-5 py-3">{(j.records_ingested as number)?.toLocaleString() ?? 0}</td>
                    <td className="px-5 py-3 text-muted-foreground text-xs">
                      {started ? started.toLocaleString() : '—'}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground text-xs">{durationSec}s</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
