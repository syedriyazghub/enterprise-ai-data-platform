'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Bell, Mail, MessageSquare, Webhook, Send, CheckCircle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

const NOTIFICATION_URL = process.env.NEXT_PUBLIC_NOTIFICATION_URL || 'http://localhost:8007';

const CHANNELS = [
  { id: 'email',   label: 'Email',            icon: <Mail className="h-4 w-4" />,           placeholder: 'recipient@example.com' },
  { id: 'slack',   label: 'Slack Webhook',    icon: <MessageSquare className="h-4 w-4" />,  placeholder: 'https://hooks.slack.com/…' },
  { id: 'teams',   label: 'Microsoft Teams',  icon: <MessageSquare className="h-4 w-4" />,  placeholder: 'https://outlook.office.com/webhook/…' },
  { id: 'webhook', label: 'Generic Webhook',  icon: <Webhook className="h-4 w-4" />,        placeholder: 'https://your-endpoint.com/notify' },
];

interface TestResult { channel: string; success: boolean; error?: string }

export default function NotificationsPage() {
  const [channel, setChannel] = useState('email');
  const [recipient, setRecipient] = useState('');
  const [title, setTitle] = useState('Test Notification');
  const [body, setBody] = useState('This is a test notification from AI Data Platform.');
  const [severity, setSeverity] = useState<'info' | 'warning' | 'error' | 'success'>('info');
  const [results, setResults] = useState<TestResult[]>([]);

  const sendMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${NOTIFICATION_URL}/api/v1/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel, recipient, title, body, severity }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: (data) => {
      setResults((prev) => [{ channel, success: data.success }, ...prev.slice(0, 9)]);
      toast[data.success ? 'success' : 'error'](
        data.success ? 'Notification sent' : 'Notification failed'
      );
    },
    onError: (err: Error) => {
      setResults((prev) => [{ channel, success: false, error: err.message }, ...prev.slice(0, 9)]);
      toast.error('Failed to send notification');
    },
  });

  const selectedChannel = CHANNELS.find((c) => c.id === channel)!;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Notifications</h1>
        <p className="text-muted-foreground">Configure and test notification channels</p>
      </div>

      {/* Channel Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {CHANNELS.map((c) => (
          <button
            key={c.id}
            onClick={() => setChannel(c.id)}
            className={cn(
              'flex flex-col items-center gap-2 p-4 rounded-lg border transition-colors text-sm',
              channel === c.id
                ? 'border-primary bg-primary/5 text-primary'
                : 'border-border bg-card hover:bg-accent text-muted-foreground'
            )}
          >
            {c.icon}
            <span className="text-xs font-medium">{c.label}</span>
          </button>
        ))}
      </div>

      {/* Test Form */}
      <div className="rounded-lg border border-border bg-card p-5 space-y-4">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Bell className="h-4 w-4" /> Send Test Notification via {selectedChannel.label}
        </h2>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Recipient</label>
            <input
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder={selectedChannel.placeholder}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Severity</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value as typeof severity)}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {['info', 'success', 'warning', 'error'].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Message</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>
        </div>

        <button
          onClick={() => sendMutation.mutate()}
          disabled={!recipient || sendMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {sendMutation.isPending
            ? <><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Sending…</>
            : <><Send className="h-4 w-4" /> Send Test</>
          }
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-5 py-3 border-b border-border text-sm font-medium">Recent Results</div>
          <ul className="divide-y divide-border">
            {results.map((r, i) => (
              <li key={i} className="flex items-center gap-3 px-5 py-3">
                {r.success
                  ? <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
                  : <XCircle className="h-4 w-4 text-red-500 shrink-0" />
                }
                <span className="text-sm capitalize">{r.channel}</span>
                {r.error && <span className="text-xs text-red-400 ml-auto">{r.error}</span>}
                {r.success && <span className="text-xs text-green-500 ml-auto">Delivered</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
