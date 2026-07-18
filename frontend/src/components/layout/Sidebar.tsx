'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard, Database, GitBranch, ShieldCheck,
  Brain, BarChart3, Bell, Settings, Upload, FileText,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/sources', label: 'Data Sources', icon: Database },
  { href: '/dashboard/upload', label: 'Upload', icon: Upload },
  { href: '/dashboard/pipelines', label: 'Pipelines', icon: GitBranch },
  { href: '/dashboard/validation', label: 'Validation', icon: ShieldCheck },
  { href: '/dashboard/ai-chat', label: 'AI Assistant', icon: Brain },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/reports', label: 'Reports', icon: FileText },
  { href: '/dashboard/notifications', label: 'Notifications', icon: Bell },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5 border-b border-border">
        <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
          <Brain className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <p className="text-sm font-bold leading-none">AI Data Platform</p>
          <p className="text-xs text-muted-foreground">Enterprise Edition</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              pathname === href
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-border">
        <p className="text-xs text-muted-foreground">v1.0.0 · MIT License</p>
      </div>
    </aside>
  );
}
