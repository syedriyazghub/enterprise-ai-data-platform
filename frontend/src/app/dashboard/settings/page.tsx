'use client';

import { useQuery } from '@tanstack/react-query';
import { Settings, Server, Activity, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const SERVICES = [
  { name: 'Ingestion Service',      url: process.env.NEXT_PUBLIC_INGESTION_URL  || 'http://localhost:8001', port: 8001 },
  { name: 'Validation Service',     url: process.env.NEXT_PUBLIC_VALIDATION_URL || 'http://localhost:8002', port: 8002 },
  { name: 'AI Service',             url: process.env.NEXT_PUBLIC_AI_SERVICE_URL || 'http://localhost:8004', port: 8004 },
  { name: 'Analytics Service',      url: process.env.NEXT_PUBLIC_ANALYTICS_URL  || 'http://localhost:8008', port: 8008 },
];

function ServiceHealthCard({ service }: { service: typeof SERVICES[0] }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health', service.port],
    queryFn: async () => {
      const res = await fetch(`${service.url}/health`);
      if (!res.ok) throw new Error('unhealthy');
      return res.json();
    },
    refetchInterval: 30_000,
    retry: 1,
  });

  return (
    <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-card">
      <div className="flex items-center gap-3">
        <Server className="h-4 w-4 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">{service.name}</p>
          <p className="text-xs text-muted-foreground">:{service.port}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
        {!isLoading && !isError && (
          <span className="flex items-center gap-1 text-xs text-green-500">
            <CheckCircle className="h-3.5 w-3.5" /> Healthy
          </span>
        )}
        {!isLoading && isError && (
          <span className="flex items-center gap-1 text-xs text-red-500">
            <XCircle className="h-3.5 w-3.5" /> Unreachable
          </span>
        )}
      </div>
    </div>
  );
}

const FEATURE_FLAGS = [
  { key: 'ENABLE_AI_FEATURES',   label: 'AI Features',        description: 'Document intelligence, RAG, anomaly detection' },
  { key: 'ENABLE_OCR',           label: 'OCR Processing',     description: 'Tesseract OCR for scanned PDFs' },
  { key: 'ENABLE_STREAMING',     label: 'Streaming ETL',      description: 'Kafka/RabbitMQ real-time ingestion' },
  { key: 'ENABLE_MULTI_TENANT',  label: 'Multi-Tenancy',      description: 'Tenant isolation and RBAC' },
  { key: 'ENABLE_AUDIT_LOG',     label: 'Audit Logging',      description: 'Full audit trail for all operations' },
];

export default function SettingsPage() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Platform configuration and service health</p>
      </div>

      {/* Service Health */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Activity className="h-4 w-4" /> Service Health
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SERVICES.map((s) => <ServiceHealthCard key={s.port} service={s} />)}
        </div>
      </section>

      {/* Feature Flags */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Settings className="h-4 w-4" /> Feature Flags
        </h2>
        <div className="rounded-lg border border-border bg-card divide-y divide-border">
          {FEATURE_FLAGS.map((flag) => (
            <div key={flag.key} className="flex items-center justify-between px-5 py-4">
              <div>
                <p className="text-sm font-medium">{flag.label}</p>
                <p className="text-xs text-muted-foreground">{flag.description}</p>
              </div>
              <span className="text-xs font-mono text-muted-foreground bg-secondary px-2 py-1 rounded">
                {flag.key}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Feature flags are configured via environment variables in <code className="font-mono">.env</code>.
        </p>
      </section>

      {/* Platform Info */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold">Platform Information</h2>
        <div className="rounded-lg border border-border bg-card divide-y divide-border">
          {[
            { label: 'Version',      value: '1.0.0' },
            { label: 'Environment',  value: process.env.NODE_ENV ?? 'development' },
            { label: 'Frontend',     value: 'Next.js 14 · React 18 · TypeScript' },
            { label: 'Backend',      value: 'FastAPI · ASP.NET Core 8' },
            { label: 'Databases',    value: 'PostgreSQL · MongoDB · Redis · ChromaDB' },
            { label: 'Observability',value: 'Prometheus · Grafana · Jaeger · ELK' },
          ].map((row) => (
            <div key={row.label} className="flex items-center justify-between px-5 py-3">
              <span className="text-sm text-muted-foreground">{row.label}</span>
              <span className="text-sm font-medium">{row.value}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
