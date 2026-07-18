'use client';

import { useQuery } from '@tanstack/react-query';
import { ingestionApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  completed: 'text-green-500 bg-green-500/10',
  running:   'text-blue-500 bg-blue-500/10',
  failed:    'text-red-500 bg-red-500/10',
  pending:   'text-yellow-500 bg-yellow-500/10',
  cancelled: 'text-gray-500 bg-gray-500/10',
};

export function RecentJobsTable() {
  const { data, isLoading } = useQuery({
    queryKey: ['recent-jobs'],
    queryFn: () => ingestionApi.getJobs(1),
    refetchInterval: 15_000,
  });

  const jobs: Record<string, unknown>[] = (data?.items ?? []).slice(0, 8);

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold">Recent Ingestion Jobs</h3>
        {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="px-5 py-3 text-left font-medium">Job ID</th>
              <th className="px-5 py-3 text-left font-medium">Status</th>
              <th className="px-5 py-3 text-right font-medium">Records</th>
              <th className="px-5 py-3 text-right font-medium">Duration</th>
              <th className="px-5 py-3 text-right font-medium">Started</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            ) : jobs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">
                  No jobs yet. Trigger a pipeline to see results here.
                </td>
              </tr>
            ) : (
              jobs.map((job) => {
                const status = job.status as string;
                const started = job.started_at ? new Date(job.started_at as string) : null;
                const completed = job.completed_at ? new Date(job.completed_at as string) : null;
                const durationSec =
                  started && completed
                    ? `${((completed.getTime() - started.getTime()) / 1000).toFixed(1)}s`
                    : status === 'running' ? 'Running…' : '—';

                return (
                  <tr
                    key={job.id as string}
                    className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors"
                  >
                    <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                      {(job.id as string).slice(0, 8)}…
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                          STATUS_COLORS[status] ?? STATUS_COLORS.pending
                        )}
                      >
                        {status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      {((job.records_ingested as number) ?? 0).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-right text-muted-foreground text-xs">
                      {durationSec}
                    </td>
                    <td className="px-5 py-3 text-right text-muted-foreground text-xs">
                      {started ? started.toLocaleTimeString() : '—'}
                    </td>
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
