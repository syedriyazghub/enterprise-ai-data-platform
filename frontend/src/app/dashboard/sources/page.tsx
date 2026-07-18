'use client';

import { useQuery } from '@tanstack/react-query';
import { ingestionApi } from '@/lib/api';
import { Plus, RefreshCw, TestTube } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';

export default function SourcesPage() {
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['sources'],
    queryFn: () => ingestionApi.getSources(),
  });

  const testConnection = async (id: string) => {
    try {
      const res = await ingestionApi.testConnection(id);
      toast[res.connected ? 'success' : 'error'](
        res.connected ? 'Connection successful' : 'Connection failed'
      );
    } catch {
      toast.error('Connection test failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Data Sources</h1>
          <p className="text-muted-foreground">Manage your registered data source connections</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => refetch()} className="p-2 rounded-md border border-border hover:bg-accent transition-colors">
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> Add Source
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="px-5 py-3 text-left font-medium">Name</th>
              <th className="px-5 py-3 text-left font-medium">Type</th>
              <th className="px-5 py-3 text-left font-medium">Status</th>
              <th className="px-5 py-3 text-left font-medium">Created</th>
              <th className="px-5 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">Loading…</td></tr>
            ) : (data?.items ?? []).length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">No sources registered yet.</td></tr>
            ) : (
              (data?.items ?? []).map((s: Record<string, unknown>) => (
                <tr key={s.id as string} className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors">
                  <td className="px-5 py-3 font-medium">{s.name as string}</td>
                  <td className="px-5 py-3 text-muted-foreground">{s.source_type as string}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.is_active ? 'text-green-500 bg-green-500/10' : 'text-red-500 bg-red-500/10'}`}>
                      {s.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-muted-foreground">
                    {new Date(s.created_at as string).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => testConnection(s.id as string)}
                      className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-border hover:bg-accent transition-colors"
                    >
                      <TestTube className="h-3 w-3" /> Test
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
