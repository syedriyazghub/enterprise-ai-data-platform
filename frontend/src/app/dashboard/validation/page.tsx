'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { validationApi } from '@/lib/api';
import { ShieldCheck, Play, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

const SAMPLE_RECORDS = [
  { name: 'Alice', email: 'alice@example.com', phone: '+919876543210', pan: 'ABCDE1234F', age: '28' },
  { name: 'Bob',   email: 'not-an-email',       phone: '12345',         pan: 'INVALID',    age: '200' },
  { name: '',      email: 'carol@example.com',  phone: '+919876543211', pan: 'FGHIJ5678K', age: '35' },
];

const SAMPLE_RULES = [
  { field: 'name',  rule_type: 'not_null',      severity: 'error',   params: {} },
  { field: 'email', rule_type: 'email',          severity: 'error',   params: {} },
  { field: 'phone', rule_type: 'phone',          severity: 'warning', params: { country: 'IN' } },
  { field: 'pan',   rule_type: 'pan',            severity: 'error',   params: {} },
  { field: 'age',   rule_type: 'numeric_range',  severity: 'error',   params: { min: 0, max: 150 } },
];

export default function ValidationPage() {
  const [records, setRecords] = useState(JSON.stringify(SAMPLE_RECORDS, null, 2));
  const [rules, setRules] = useState(JSON.stringify(SAMPLE_RULES, null, 2));
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const { data: availableRules } = useQuery({
    queryKey: ['validation-rules'],
    queryFn: () => validationApi.getRules(),
  });

  const validateMutation = useMutation({
    mutationFn: ({ r, ru }: { r: unknown[]; ru: unknown[] }) =>
      validationApi.validate(r as Record<string, unknown>[], ru as Record<string, unknown>[]),
    onSuccess: (data) => {
      setResult(data);
      toast.success(`Validation complete — ${data.quality_score}% quality score`);
    },
    onError: () => toast.error('Validation failed'),
  });

  const handleValidate = () => {
    try {
      const r = JSON.parse(records);
      const ru = JSON.parse(rules);
      validateMutation.mutate({ r, ru });
    } catch {
      toast.error('Invalid JSON in records or rules');
    }
  };

  const scoreColor = (score: number) =>
    score >= 90 ? 'text-green-500' : score >= 70 ? 'text-yellow-500' : 'text-red-500';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Validation Explorer</h1>
        <p className="text-muted-foreground">Test validation rules against your data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Records Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Records (JSON array)</label>
          <textarea
            value={records}
            onChange={(e) => setRecords(e.target.value)}
            rows={12}
            className="w-full rounded-lg border border-border bg-card px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          />
        </div>

        {/* Rules Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Validation Rules (JSON array)</label>
          <textarea
            value={rules}
            onChange={(e) => setRules(e.target.value)}
            rows={12}
            className="w-full rounded-lg border border-border bg-card px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          />
        </div>
      </div>

      <button
        onClick={handleValidate}
        disabled={validateMutation.isPending}
        className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
      >
        {validateMutation.isPending
          ? <><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Validating…</>
          : <><Play className="h-4 w-4" /> Run Validation</>
        }
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: 'Quality Score', value: `${result.quality_score}%`, icon: <ShieldCheck className="h-4 w-4" />, color: scoreColor(result.quality_score as number) },
              { label: 'Passed', value: result.passed_records, icon: <CheckCircle className="h-4 w-4 text-green-500" />, color: 'text-green-500' },
              { label: 'Failed', value: result.failed_records, icon: <XCircle className="h-4 w-4 text-red-500" />, color: 'text-red-500' },
              { label: 'Warnings', value: result.total_warnings, icon: <AlertTriangle className="h-4 w-4 text-yellow-500" />, color: 'text-yellow-500' },
            ].map((kpi) => (
              <div key={kpi.label} className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">{kpi.label}</span>
                  {kpi.icon}
                </div>
                <p className={cn('text-xl font-bold', kpi.color)}>{kpi.value as string}</p>
              </div>
            ))}
          </div>

          {/* Per-record results */}
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <div className="px-5 py-3 border-b border-border text-sm font-medium">
              Record-level Results
            </div>
            <div className="divide-y divide-border max-h-80 overflow-y-auto">
              {((result.reports as unknown[]) ?? []).map((report: unknown) => {
                const r = report as Record<string, unknown>;
                return (
                  <div key={r.record_index as number} className="px-5 py-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium">Record #{(r.record_index as number) + 1}</span>
                      <span className={cn('text-xs font-medium', r.passed ? 'text-green-500' : 'text-red-500')}>
                        {r.passed ? '✓ Passed' : '✗ Failed'} · {r.quality_score as number}%
                      </span>
                    </div>
                    {((r.errors as unknown[]) ?? []).map((e: unknown, i: number) => {
                      const err = e as Record<string, unknown>;
                      return (
                        <p key={i} className="text-xs text-red-400 mt-0.5">
                          [{err.field as string}] {err.message as string}
                        </p>
                      );
                    })}
                    {((r.warnings as unknown[]) ?? []).map((w: unknown, i: number) => {
                      const warn = w as Record<string, unknown>;
                      return (
                        <p key={i} className="text-xs text-yellow-400 mt-0.5">
                          [{warn.field as string}] {warn.message as string}
                        </p>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Available Rules Reference */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-5 py-3 border-b border-border text-sm font-medium">
          Available Validators ({availableRules?.total ?? 0})
        </div>
        <div className="flex flex-wrap gap-2 p-4">
          {(availableRules?.rules ?? []).map((r: Record<string, string>) => (
            <span
              key={r.type}
              className="px-2 py-1 text-xs rounded-md bg-secondary text-secondary-foreground font-mono"
            >
              {r.type}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
